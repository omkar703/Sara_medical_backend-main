"""Doctor patient documents viewing with permission-based access control"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.document import Document
from app.schemas.medical_history import MedicalHistoryResponse
from app.services.permission_service import PermissionService
from app.services.minio_service import minio_service
from app.services.audit_service import log_action

router = APIRouter(prefix="/doctor", tags=["Doctor - Patient Records"])


@router.get("/patients/{patient_id}/documents", response_model=List[MedicalHistoryResponse])
async def get_patient_documents(
    patient_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    """
    Get patient medical documents with strict permission checking.
    
    HIPAA Compliance:
    - Returns 403 if doctor doesn't have permission
    - All access attempts are audit logged
    - Returns presigned URLs with 15-minute expiration
    """
    
    # Verify doctor role
    if current_user.role != "doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Doctor role required"
        )
    
    # Check permission
    permission_service = PermissionService(db)
    has_permission = await permission_service.check_doctor_access(
        doctor_id=current_user.id,
        patient_id=patient_id
    )
    
    if not has_permission:
        # Audit log unauthorized access attempt
        await log_action(
            db=db,
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            action="access_denied",
            resource_type="patient_medical_records",
            resource_id=patient_id,
            request=request,
            metadata={"reason": "No active permission grant or appointment"}
        )
        await db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to medical records not granted by patient"
        )
    
    # Fetch documents
    query = select(Document).where(
        Document.patient_id == patient_id,
        Document.deleted_at.is_(None)
    ).order_by(Document.uploaded_at.desc())
    
    result = await db.execute(query)
    documents = result.scalars().all()
    
    # Audit log successful access
    await log_action(
        db=db,
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        action="view",
        resource_type="patient_medical_records",
        resource_id=patient_id,
        request=request,
        metadata={"document_count": len(documents)}
    )
    await db.commit()
    
    # Generate presigned URLs for each document
    response_documents = []
    for doc in documents:
        presigned_url = minio_service.generate_presigned_url(
            "saramedico-medical-records",
            doc.storage_path,
            expiry_seconds=900  # 15 minutes
        )
        
        if not presigned_url:
            presigned_url = f"[URL generation failed]"
        
        response_documents.append(MedicalHistoryResponse(
            id=doc.id,
            file_name=doc.file_name,
            category=doc.category or "OTHER",
            title=doc.title,
            notes=doc.notes,
            file_size=doc.file_size,
            uploaded_at=doc.uploaded_at,
            presigned_url=presigned_url
        ))
    
    return response_documents
