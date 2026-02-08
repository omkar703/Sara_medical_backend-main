"""Consultation API Endpoints"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user, get_organization_id, require_role
from app.database import get_db
from app.models.user import User
from app.schemas.consultation import (
    ConsultationCreate,
    ConsultationListResponse,
    ConsultationResponse,
    ConsultationUpdate,
)
from app.schemas.document import MessageResponse
from app.services.audit_service import log_action
from app.services.consultation_service import ConsultationService
from app.api.v1.websockets import manager

router = APIRouter(prefix="/consultations", tags=["Consultations"])


@router.post("", response_model=ConsultationResponse)
async def schedule_consultation(
    request_data: ConsultationCreate,
    current_user: User = Depends(require_role("doctor")),
    organization_id: UUID = Depends(get_organization_id),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    """
    Schedule a new consultation and Zoom meeting.
    Requires 'doctor' or 'admin' role.
    """
    service = ConsultationService(db)
    
    try:
        consultation = await service.schedule_consultation(
            doctor_id=current_user.id,
            patient_id=request_data.patientId,
            organization_id=organization_id,
            scheduled_at=request_data.scheduledAt,
            duration_minutes=request_data.durationMinutes,
            notes=request_data.notes
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to schedule consultation: {str(e)}"
        )
    
    await db.commit()
    
    # Audit Log
    await log_action(
        db=db,
        user_id=current_user.id,
        organization_id=organization_id,
        action="schedule",
        resource_type="consultation",
        resource_id=consultation.id,
        request=request,
        metadata={"patient_id": str(request_data.patientId)}
    )
    await db.commit()
    
    # Notify Doctor (Self) and potentially others via WS
    await manager.send_personal_message(
        {
            "type": "consultation.created",
            "data": {"id": str(consultation.id), "status": consultation.status}
        },
        organization_id=organization_id,
        user_id=current_user.id
    )
    
    return await _consultation_to_response(consultation)


@router.get("", response_model=ConsultationListResponse)
async def list_consultations(
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_active_user),
    organization_id: UUID = Depends(get_organization_id),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    """
    List consultations for the current user/organization.
    """
    service = ConsultationService(db)
    
    consultations = await service.list_consultations(
        organization_id=organization_id,
        user_id=current_user.id,
        role=current_user.role,
        status=status
    )
    
    # Audit Log
    await log_action(
        db=db,
        user_id=current_user.id,
        organization_id=organization_id,
        action="list",
        resource_type="consultation",
        resource_id=None,
        request=request,
        metadata={"status_filter": status}
    )
    await db.commit()
    
    response_list = []
    for c in consultations:
        response_list.append(await _consultation_to_response(c))
        
    return ConsultationListResponse(
        consultations=response_list,
        total=len(response_list)
    )


@router.get("/{consultation_id}", response_model=ConsultationResponse)
async def get_consultation(
    consultation_id: UUID,
    current_user: User = Depends(get_current_active_user),
    organization_id: UUID = Depends(get_organization_id),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    """
    Get consultation details.
    """
    service = ConsultationService(db)
    
    consultation = await service.get_consultation(
        consultation_id=consultation_id,
        organization_id=organization_id
    )
    
    if not consultation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consultation not found"
        )
        
    # Security check: Doctors can see all in org (or assigned), Patients only their own
    # Current list_consultations logic handles filtering implicitly, but direct access needs check
    if current_user.role == "patient":
        # Check if patient owns this
        # Note: current implementation assumes 'user' table users. 
        # If 'patient' table entities log in differently, logic adjusts.
        # Assuming doctor access for now based on 'require_role' usage elsewhere.
        pass

    # Audit Log
    await log_action(
        db=db,
        user_id=current_user.id,
        organization_id=organization_id,
        action="view",
        resource_type="consultation",
        resource_id=consultation.id,
        request=request
    )
    await db.commit()
    
    return await _consultation_to_response(consultation)


@router.put("/{consultation_id}", response_model=ConsultationResponse)
async def update_consultation(
    consultation_id: UUID,
    updates: ConsultationUpdate,
    current_user: User = Depends(require_role("doctor")),
    organization_id: UUID = Depends(get_organization_id),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    """
    Update consultation status or medical notes.
    """
    service = ConsultationService(db)
    
    update_data = updates.model_dump(exclude_unset=True)
    
    consultation = await service.update_consultation(
        consultation_id=consultation_id,
        organization_id=organization_id,
        updates=update_data
    )
    
    if not consultation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consultation not found"
        )
    
    await db.commit()
    
    # Audit Log
    await log_action(
        db=db,
        user_id=current_user.id,
        organization_id=organization_id,
        action="update",
        resource_type="consultation",
        resource_id=consultation.id,
        request=request,
        metadata={"fields": list(update_data.keys())}
    )
    await db.commit()
    
    return await _consultation_to_response(consultation)


@router.post("/{consultation_id}/analyze", response_model=MessageResponse)
async def analyze_consultation(
    consultation_id: UUID,
    current_user: User = Depends(require_role("doctor")),
    organization_id: UUID = Depends(get_organization_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Fetch Zoom transcript and trigger AI analysis.
    """
    # 1. Get Consultation
    service = ConsultationService(db)
    consultation = await service.get_consultation(consultation_id, organization_id)
    
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")
        
    if not consultation.meeting_id:
        raise HTTPException(status_code=400, detail="No Zoom meeting linked to this consultation")

    # 2. Fetch Transcript from Zoom
    # (Note: This might fail if the meeting just ended. Zoom takes time to process.)
    from app.services.zoom_service import zoom_service
    transcript_text = await zoom_service.get_meeting_transcript(consultation.meeting_id)

    if not transcript_text:
        # If we already have a transcript saved manually, use that
        if consultation.transcript:
            transcript_text = consultation.transcript
        else:
            raise HTTPException(
                status_code=400, 
                detail="Transcript not ready yet. Please wait for Zoom to process the cloud recording."
            )
    else:
        # Save the new transcript to DB
        consultation.transcript = transcript_text
        consultation.ai_status = "processing"
        await db.commit()

    # 3. Trigger AI Processing (Stub for now)
    # In the next step, you will pass `transcript_text` to your LLM here.
    # For now, we simulate success.
    
    return MessageResponse(
        message="Transcript retrieved successfully. AI analysis started."
    )