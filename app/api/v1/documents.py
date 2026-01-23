"""Document API Endpoints"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user, get_organization_id, require_role
from app.database import get_db
from app.models.user import User
from app.schemas.document import (
    DocumentConfirmRequest,
    DocumentListResponse,
    DocumentResponse,
    DocumentUploadRequest,
    DocumentUploadResponse,
    MessageResponse,
)
from app.services.audit_service import log_action
from app.services.document_service import DocumentService
from app.services.storage_service import StorageService

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload-url", response_model=DocumentUploadResponse)
async def request_upload_url(
    request_data: DocumentUploadRequest,
    current_user: User = Depends(require_role("doctor")),
    organization_id: UUID = Depends(get_organization_id),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    """
    Request a presigned upload URL for document upload.
    Requires 'doctor' or 'admin' role.
    """
    service = DocumentService(db)
    storage = StorageService()
    
    # Create document metadata
    document_metadata = await service.create_document_metadata(
        patient_id=request_data.patientId,
        organization_id=organization_id,
        file_name=request_data.fileName,
        file_type=request_data.fileType,
        file_size=request_data.fileSize,
        uploaded_by=current_user.id,
    )
    
    # Generate presigned upload URL
    upload_url = await storage.generate_upload_url(
        storage_path=document_metadata["storage_path"],
        content_type=request_data.fileType,
        expires_in=3600
    )
    
    await db.commit()
    
    # Audit log
    await log_action(
        db=db,
        user_id=current_user.id,
        organization_id=organization_id,
        action="request_upload",
        resource_type="document",
        resource_id=UUID(document_metadata["id"]),
        request=request,
        metadata={
            "file_name": request_data.fileName,
            "file_size": request_data.fileSize,
            "patient_id": str(request_data.patientId)
        }
    )
    await db.commit()
    
    return DocumentUploadResponse(
        uploadUrl=upload_url,
        documentId=document_metadata["id"],
        expiresIn=3600
    )


@router.post("/{document_id}/confirm", response_model=DocumentResponse)
async def confirm_upload(
    document_id: UUID,
    confirm_data: DocumentConfirmRequest,
    current_user: User = Depends(require_role("doctor")),
    organization_id: UUID = Depends(get_organization_id),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    """
    Confirm document upload and update metadata.
    Requires 'doctor' or 'admin' role.
    """
    service = DocumentService(db)
    
    # Confirm upload with metadata
    document = await service.confirm_upload(
        document_id=document_id,
        organization_id=organization_id,
        metadata=confirm_data.metadata
    )
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    await db.commit()
    
    # Audit log
    await log_action(
        db=db,
        user_id=current_user.id,
        organization_id=organization_id,
        action="upload",
        resource_type="document",
        resource_id=document_id,
        request=request,
        metadata={"confirmed": True}
    )
    await db.commit()
    
    # TODO: Trigger virus scan Celery task
    # from app.workers.tasks import scan_document_for_viruses
    # scan_document_for_viruses.delay(str(document_id))
    
    return DocumentResponse(**document)


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    patient_id: Optional[UUID] = Query(None, description="Filter by patient ID"),
    category: Optional[str] = Query(None, description="Filter by category"),
    current_user: User = Depends(get_current_active_user),
    organization_id: UUID = Depends(get_organization_id),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    """
    List documents for the current organization.
    Optionally filter by patient or category.
    """
    service = DocumentService(db)
    
    documents = await service.list_documents(
        organization_id=organization_id,
        patient_id=patient_id,
        category=category
    )
    
    # Audit log
    await log_action(
        db=db,
        user_id=current_user.id,
        organization_id=organization_id,
        action="list",
        resource_type="document",
        resource_id=None,
        request=request,
        metadata={"patient_id": str(patient_id) if patient_id else None, "category": category}
    )
    await db.commit()
    
    return DocumentListResponse(
        documents=[DocumentResponse(**doc) for doc in documents],
        total=len(documents)
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    current_user: User = Depends(get_current_active_user),
    organization_id: UUID = Depends(get_organization_id),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    """
    Get document details by ID with download URL.
    """
    service = DocumentService(db)
    
    document = await service.get_document(
        document_id=document_id,
        organization_id=organization_id
    )
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Audit log
    await log_action(
        db=db,
        user_id=current_user.id,
        organization_id=organization_id,
        action="view",
        resource_type="document",
        resource_id=document_id,
        request=request
    )
    await db.commit()
    
    return DocumentResponse(**document)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    current_user: User = Depends(require_role("doctor")),
    organization_id: UUID = Depends(get_organization_id),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    """
    Soft delete a document.
    Requires 'doctor' or 'admin' role.
    """
    service = DocumentService(db)
    
    success = await service.delete_document(
        document_id=document_id,
        organization_id=organization_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    await db.commit()
    
    # Audit log
    await log_action(
        db=db,
        user_id=current_user.id,
        organization_id=organization_id,
        action="delete",
        resource_type="document",
        resource_id=document_id,
        request=request
    )
    await db.commit()
    
    return None


@router.post("/{document_id}/analyze", response_model=MessageResponse)
async def analyze_document(
    document_id: UUID,
    current_user: User = Depends(get_current_active_user),
    organization_id: UUID = Depends(get_organization_id),
    db: AsyncSession = Depends(get_db),
):
    """
    AI document analysis endpoint (STUB - Future implementation)
    
    This endpoint will be implemented in future phases for OCR/RAG functionality.
    """
    return MessageResponse(
        message="AI document analysis feature coming soon. This is a placeholder endpoint."
    )
