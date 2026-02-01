"""Medical History API - HIPAA-compliant patient document upload"""

import os
import uuid
from uuid import UUID
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User
from app.models.document import Document
from app.models.patient import Patient
from app.schemas.medical_history import MedicalHistoryResponse, DocumentCategory
from app.services.minio_service import minio_service
from app.services.audit_service import log_action

router = APIRouter(prefix="/doctor/medical-history", tags=["Medical History"])

# Allowed file extensions for medical documents
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".dicom", ".dcm"}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB


@router.post("", response_model=MedicalHistoryResponse, status_code=status.HTTP_201_CREATED)
async def upload_medical_history(
    file: UploadFile = File(...),
    patient_id: UUID = Form(...),
    category: str = Form(...),
    title: str = Form(None),
    description: str = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("doctor")),
    request: Request = None
):
    """
    Upload patient medical history document (Doctor only).
    Only the doctor who onboarded the patient can upload documents.
    """
    
    # Validate file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Read file content
    file_content = await file.read()
    file_size = len(file_content)
    
    # Validate file size
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE / (1024*1024)}MB"
        )
    
    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty"
        )
    
    # Verify category
    try:
        doc_category = DocumentCategory(category)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid category. Allowed: {', '.join([c.value for c in DocumentCategory])}"
        )
    
    # Get patient record and verify ownership
    patient_query = select(Patient).where(
        Patient.id == patient_id,
        Patient.data_is_deleted == False if hasattr(Patient, "data_is_deleted") else Patient.deleted_at.is_(None)
    )
    # Using getattr generic check or just deleted_at since I saw it in view_file
    patient_query = select(Patient).where(
        Patient.id == patient_id,
        Patient.deleted_at.is_(None)
    )
    
    patient_result = await db.execute(patient_query)
    patient = patient_result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
        
    # Security Check: Creator Only
    if patient.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: Only the doctor who onboarded this patient can upload medical history."
        )

    # Ensure patient belongs to same organization (double check)
    if patient.organization_id != current_user.organization_id:
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: Patient belongs to a different organization."
        )
    
    # Generate unique storage path
    unique_id = uuid.uuid4()
    storage_path = f"medical-records/{current_user.organization_id}/{patient.id}/{unique_id}{file_ext}"
    
    # Upload to MinIO (medical-records bucket)
    upload_success = minio_service.upload_bytes(
        file_content,
        "saramedico-medical-records",
        storage_path,
        content_type=file.content_type or "application/octet-stream"
    )
    
    if not upload_success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file to storage"
        )
    
    # Create document record
    document = Document(
        patient_id=patient.id,
        organization_id=current_user.organization_id,
        file_name=file.filename,
        file_type=file.content_type or "application/octet-stream",
        file_size=file_size,
        storage_path=storage_path,
        category=doc_category.value,
        title=title,
        notes=description,
        uploaded_by=current_user.id,
        virus_scanned=False  # TODO: Integrate virus scanning
    )
    
    db.add(document)
    await db.commit()
    await db.refresh(document)
    
    # Audit log
    await log_action(
        db=db,
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        action="upload",
        resource_type="medical_document",
        resource_id=document.id,
        request=request,
        metadata={
            "file_name": file.filename,
            "category": category,
            "file_size": file_size,
            "patient_id": str(patient.id)
        }
    )
    await db.commit()
    
    # Generate presigned URL (15-minute expiration)
    presigned_url = minio_service.generate_presigned_url(
        "saramedico-medical-records",
        storage_path,
        expiry_seconds=900  # 15 minutes
    )
    
    if not presigned_url:
        presigned_url = f"[Presigned URL generation failed for {storage_path}]"
    
    return MedicalHistoryResponse(
        id=document.id,
        file_name=document.file_name,
        category=document.category,
        title=document.title,
        notes=document.notes,
        file_size=document.file_size,
        uploaded_at=document.uploaded_at,
        presigned_url=presigned_url
    )
