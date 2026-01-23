"""AI Integration API - Queue patient data for future AI processing"""

from typing import Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.ai_processing_queue import AIProcessingQueue
from app.services.permission_service import PermissionService

router = APIRouter(prefix="/doctor/ai", tags=["AI Integration"])


class AIContributeRequest(BaseModel):
    """Request schema for AI contribution"""
    patient_id: UUID
    data_payload: Dict[str, Any] = Field(..., description="Data to be processed (file IDs, text notes, etc.)")
    request_type: str = Field("diagnosis_assist", description="Type of AI processing requested")


class AIContributeResponse(BaseModel):
    """Response schema for AI contribution"""
    queue_id: UUID
    status: str
    message: str


@router.post("/contribute", response_model=AIContributeResponse, status_code=status.HTTP_201_CREATED)
async def contribute_to_ai(
    request: AIContributeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Queue patient data for AI processing.
    
    HIPAA Compliance:
    - Verifies doctor has permission to access patient data
    - Tags queue entry with patient_id for privacy tracking
    - Maintains audit trail for AI data usage
    """
    
    # Verify doctor role
    if current_user.role != "doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Doctor role required"
        )
    
    # Check permission to access patient data
    permission_service = PermissionService(db)
    has_permission = await permission_service.check_doctor_access(
        doctor_id=current_user.id,
        patient_id=request.patient_id
    )
    
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to patient data not granted. Cannot submit to AI queue."
        )
    
    # Create AI processing queue entry
    queue_entry = AIProcessingQueue(
        patient_id=request.patient_id,
        doctor_id=current_user.id,
        organization_id=current_user.organization_id,
        data_payload=request.data_payload,
        request_type=request.request_type,
        status="pending"
    )
    
    db.add(queue_entry)
    await db.commit()
    await db.refresh(queue_entry)
    
    return AIContributeResponse(
        queue_id=queue_entry.id,
        status="pending",
        message=f"Data queued for AI processing. Queue ID: {queue_entry.id}"
    )
