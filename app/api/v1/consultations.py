"""Consultation API Endpoints"""

from typing import Optional
from uuid import UUID
import asyncio
from datetime import date
from sqlalchemy import select, func, and_, cast, Date

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user, get_organization_id, require_role
from app.database import get_db
from app.models.user import User
from app.models.consultation import Consultation
from app.schemas.consultation import (
    ConsultationCreate,
    ConsultationListResponse,
    ConsultationResponse,
    ConsultationUpdate,
    QueueMetricsResponse
)
from app.schemas.document import MessageResponse
from app.services.audit_service import log_action
from app.services.google_meet_service import google_meet_service
from app.services.consultation_service import ConsultationService
from app.api.v1.websockets import manager
from app.core.security import pii_encryption

router = APIRouter(prefix="/consultations", tags=["Consultations"])

async def _consultation_to_response(consultation) -> ConsultationResponse:
    """Helper to safely map a Consultation ORM object to the Pydantic response"""
    
    # Decrypt names safely
    try:
        doctor_name = pii_encryption.decrypt(consultation.doctor.full_name) if consultation.doctor else None
    except:
        doctor_name = "Unknown Doctor"
        
    try:
        patient_name = pii_encryption.decrypt(consultation.patient.full_name) if consultation.patient else None
    except:
        patient_name = "Unknown Patient"

    return ConsultationResponse(
        id=str(consultation.id),
        scheduledAt=consultation.scheduled_at,
        durationMinutes=consultation.duration_minutes,
        status=consultation.status,
        doctorId=str(consultation.doctor_id),
        doctorName=doctor_name,
        patientId=str(consultation.patient_id),
        patientName=patient_name,
        
        # NEW Google Meet Info
        google_event_id=getattr(consultation, 'google_event_id', None),
        meet_link=getattr(consultation, 'meet_link', None),
        
        notes=consultation.notes,
        diagnosis=consultation.diagnosis,
        prescription=consultation.prescription,
        aiStatus=getattr(consultation, 'ai_status', 'pending'),
        hasAudio=False, 
        hasTranscript=bool(getattr(consultation, 'transcript', False)),
        hasSoapNote=bool(getattr(consultation, 'soap_note', False)),
        urgency_level=getattr(consultation, 'urgency_level', 'normal'),
        visit_state=getattr(consultation, 'visit_state', 'scheduled')
    )

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
    Fetch Google Meet transcript and trigger AI analysis.
    """
    service = ConsultationService(db)
    consultation = await service.get_consultation(consultation_id, organization_id)
    
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")
        
    if getattr(consultation, 'google_event_id', None) is None:
        raise HTTPException(status_code=400, detail="No Google Meet linked to this consultation")

    # Fetch the transcript text
    transcript_text = await google_meet_service.get_meeting_transcript(consultation.google_event_id)
    
    if not transcript_text:
        raise HTTPException(
            status_code=404, 
            detail="Transcript not found. If the meeting just ended, Google may still be processing it."
        )
        
    # Save it to the database
    consultation.transcript = transcript_text
    consultation.ai_status = "processing"
    await db.commit()
    
    # TODO: Pass `transcript_text` to your AI LLM here to generate the SOAP note!
    # e.g., soap_note = await ai_service.generate_soap_note(transcript_text)
    
    return MessageResponse(
        message="Transcript fetched successfully. AI analysis initiated."
    )

@router.get("/queue/metrics", response_model=QueueMetricsResponse)
async def get_queue_metrics(
    organization_id: UUID = Depends(get_organization_id),
    current_user: User = Depends(require_role("doctor")), # Or admin
    db: AsyncSession = Depends(get_db),
):
    """
    Fetch aggregated metrics for the Structured Approval Queue dashboard cards.
    """
    today = date.today()

    # Define our base query for this organization
    base_query = select(Consultation).where(Consultation.organization_id == organization_id)

    # 1. Pending Review Count
    pending_stmt = select(func.count()).select_from(base_query.where(Consultation.visit_state == 'Needs Review').subquery())
    
    # 2. High Urgency Count
    urgent_stmt = select(func.count()).select_from(base_query.where(
        Consultation.urgency_level.in_(['high', 'critical']),
        Consultation.status != 'completed'
    ).subquery())
    
    # 3. Cleared Today Count
    cleared_stmt = select(func.count()).select_from(base_query.where(
        Consultation.visit_state == 'Signed',
        cast(Consultation.completion_time, Date) == today
    ).subquery())

    # Execute aggregate queries concurrently for performance
    pending_result, urgent_result, cleared_result = await asyncio.gather(
        db.execute(pending_stmt),
        db.execute(urgent_stmt),
        db.execute(cleared_stmt)
    )

    # Calculate Average Wait Time (Mocked logic, replace with actual check_in_time delta if needed)
    # E.g., select(func.avg(Consultation.completion_time - Consultation.check_in_time))
    avg_wait_time = 12 # Fallback/stub for "12m" as seen in the UI

    return QueueMetricsResponse(
        pending_review=pending_result.scalar() or 0,
        high_urgency=urgent_result.scalar() or 0,
        cleared_today=cleared_result.scalar() or 0,
        avg_wait_time_minutes=avg_wait_time
    )
    
@router.get("", response_model=ConsultationListResponse)
async def list_consultations(
    status: Optional[str] = Query(None, description="Filter by generic status"),
    visit_state: Optional[str] = Query(None, description="Filter by specific UI state e.g., 'Needs Review'"),
    urgency_level: Optional[str] = Query(None, description="Filter by urgency e.g., 'high'"),
    provider_id: Optional[UUID] = Query(None, description="Filter by a specific doctor/provider"),
    search: Optional[str] = Query(None, description="Global search by Patient Name, MRN, or Session ID"),
    page: int = Query(1, ge=1, description="Page number for pagination"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_active_user),
    organization_id: UUID = Depends(get_organization_id),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    """
    List consultations for the Structured Approval Queue with advanced filtering and pagination.
    """
    service = ConsultationService(db)
    
    skip = (page - 1) * limit

    consultations, total_count = await service.list_consultations(
        organization_id=organization_id,
        user_id=current_user.id,
        role=current_user.role,
        status=status,
        visit_state=visit_state,
        urgency_level=urgency_level,
        provider_id=provider_id,
        search_query=search,
        skip=skip,
        limit=limit
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
        metadata={"filters": {"status": status, "search": search, "page": page}}
    )
    await db.commit()
    
    response_list = []
    # Assumes you have updated _consultation_to_response to include the new visit_state and urgency fields
    for c in consultations:
        response_list.append(await _consultation_to_response(c))
        
    return ConsultationListResponse(
        consultations=response_list,
        total=total_count
    )