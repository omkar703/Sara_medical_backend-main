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
from app.services.mock_google_meet import google_meet_service
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
        
    try:
        patient_dob_str = pii_encryption.decrypt(consultation.patient.date_of_birth) if consultation.patient and consultation.patient.date_of_birth else None
    except:
        patient_dob_str = None
        
    patient_mrn = consultation.patient.mrn if consultation.patient else None

    return ConsultationResponse(
        id=str(consultation.id),
        scheduledAt=consultation.scheduled_at,
        durationMinutes=consultation.duration_minutes,
        status=consultation.status,
        doctorId=str(consultation.doctor_id),
        doctorName=doctor_name,
        patientId=str(consultation.patient_id),
        patientName=patient_name,
        patientMrn=patient_mrn,
        patientDob=patient_dob_str,
        
        # NEW Google Meet Info
        googleEventId=getattr(consultation, 'google_event_id', None),
        meetLink=getattr(consultation, 'meet_link', None),
        
        notes=consultation.notes,
        diagnosis=consultation.diagnosis,
        prescription=consultation.prescription,
        aiStatus=getattr(consultation, 'ai_status', 'pending'),
        hasAudio=False, 
        hasTranscript=bool(getattr(consultation, 'transcript', False)),
        hasSoapNote=bool(getattr(consultation, 'soap_note', False)),
        urgencyLevel=getattr(consultation, 'urgency_level', 'normal'),
        visitState=getattr(consultation, 'visit_state', 'scheduled')
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

@router.delete("/{consultation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_consultation(
    consultation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("doctor")),
    organization_id: UUID = Depends(get_organization_id)
):
    """
    Delete a consultation (e.g., to clear test records).
    """
    query = select(Consultation).filter(
        and_(
            Consultation.id == consultation_id,
            Consultation.organization_id == organization_id
        )
    )
    result = await db.execute(query)
    consultation = result.scalar_one_or_none()
    
    if not consultation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consultation not found"
        )
        
    await db.delete(consultation)
    
    # Audit trail
    await log_action(
        db=db,
        user_id=current_user.id,
        organization_id=organization_id,
        action="delete",
        resource_type="consultation",
        resource_id=consultation.id
    )
    
    await db.commit()
    return None




@router.get("/lookup/by-patient", response_model=ConsultationResponse)
async def get_consultation_by_doctor_patient(
    patient_id: UUID = Query(..., description="Patient ID from the appointment"),
    current_user: User = Depends(get_current_active_user),
    organization_id: UUID = Depends(get_organization_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Look up the most recent consultation for the current doctor and a given patient.
    Useful when navigating from an approved appointment to the SOAP note page.
    """
    from sqlalchemy import and_
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Consultation)
        .options(selectinload(Consultation.doctor), selectinload(Consultation.patient))
        .where(
            and_(
                Consultation.doctor_id == current_user.id,
                Consultation.patient_id == patient_id,
                Consultation.organization_id == organization_id,
            )
        )
        .order_by(Consultation.scheduled_at.desc())
        .limit(1)
    )
    consultation = result.scalar_one_or_none()
    if not consultation:
        raise HTTPException(status_code=404, detail="No consultation found for this doctor-patient pair")
    return await _consultation_to_response(consultation)


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


@router.post("/{consultation_id}/complete")
async def complete_consultation(
    consultation_id: UUID,
    current_user: User = Depends(require_role("doctor")),
    organization_id: UUID = Depends(get_organization_id),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    """
    Mark a consultation as completed and trigger AI SOAP note generation.

    Call this endpoint when the Google Meet session ends.
    The AI will:
    1. Check if a real Google Meet transcript exists for the session.
    2. If transcript is found → generate a SOAP note via AWS Bedrock (Claude 3.5 Sonnet).
    3. If no transcript is found (meeting had no speech, or transcription not enabled)
       → ai_status is set to 'no_transcript'. No SOAP note is generated.

    Poll `GET /consultations/{id}/soap-note` every 5 seconds for results.
    """
    service = ConsultationService(db)

    consultation = await service.get_consultation(consultation_id, organization_id)
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")

    if consultation.status == "completed":
        return {
            "message": "Consultation was already completed.",
            "consultation_id": str(consultation_id),
            "ai_status": getattr(consultation, "ai_status", "unknown"),
            "soap_note_url": f"/api/v1/consultations/{consultation_id}/soap-note",
        }

    # Mark consultation as completed and trigger SOAP note generation background task
    await service.update_consultation(
        consultation_id=consultation_id,
        organization_id=organization_id,
        updates={"status": "completed", "ai_status": "awaiting_transcript"},
    )
    await db.commit()

    # Dispatch background Celery task to check for real transcript and generate SOAP
    from app.workers.tasks import generate_soap_note as soap_task
    soap_task.delay(str(consultation_id))

    await log_action(
        db=db,
        user_id=current_user.id,
        organization_id=organization_id,
        action="complete",
        resource_type="consultation",
        resource_id=consultation_id,
        request=request,
    )
    await db.commit()

    return {
        "message": "Consultation marked as completed. Checking for meeting transcript...",
        "consultation_id": str(consultation_id),
        "ai_status": "awaiting_transcript",
        "soap_note_url": f"/api/v1/consultations/{consultation_id}/soap-note",
        "instructions": (
            "Poll the soap_note_url every 10 seconds. "
            "Returns 202 while processing. "
            "Returns 200 with soap_note when ready. "
            "ai_status='no_transcript' means no meeting speech was detected."
        ),
    }



@router.post("/{consultation_id}/analyze")
async def analyze_consultation(
    consultation_id: UUID,
    scenario: Optional[str] = None,
    current_user: User = Depends(require_role("doctor")),
    organization_id: UUID = Depends(get_organization_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger SOAP note generation for a consultation.

    Uses a mock transcript (simulating Google Meet Transcript API) and sends it
    to AWS Bedrock (Claude) for SOAP note generation via a background Celery task.

    Query params:
        scenario (optional): One of 'chest_pain', 'diabetes', 'pediatric_fever',
                             'hypertension', 'anxiety'. Picks randomly if not set.
    """
    from app.services.mock_transcript_service import mock_transcript_service, SCENARIOS
    from app.workers.tasks import generate_soap_note as soap_task

    service = ConsultationService(db)
    consultation = await service.get_consultation(consultation_id, organization_id)

    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")

    # Validate optional scenario key
    if scenario and scenario not in SCENARIOS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid scenario '{scenario}'. Available: {list(SCENARIOS.keys())}"
        )

    # Mark as processing immediately so the caller knows something is happening
    consultation.ai_status = "processing"
    await db.commit()

    # Dispatch the background Celery task
    # The task will: get mock transcript → call Bedrock → save soap_note to DB
    soap_task.delay(str(consultation_id))

    available_scenarios = list(SCENARIOS.keys())
    return MessageResponse(
        message=(
            f"SOAP note generation queued for consultation {consultation_id}. "
            f"Processing in background. Poll GET /consultations/{consultation_id}/soap-note for results. "
            f"Available test scenarios: {available_scenarios}"
        )
    )


@router.get("/{consultation_id}/soap-note")
async def get_soap_note(
    consultation_id: UUID,
    current_user: User = Depends(get_current_active_user),
    organization_id: UUID = Depends(get_organization_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve the generated SOAP note for a consultation.

    Returns:
        200 + SOAP note JSON if generation is complete.
        202 if still processing.
        404 if consultation not found or SOAP note not yet generated.
    """
    from fastapi.responses import JSONResponse

    service = ConsultationService(db)
    consultation = await service.get_consultation(consultation_id, organization_id)

    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")

    ai_status = getattr(consultation, 'ai_status', 'pending')

    if ai_status == "processing":
        return JSONResponse(
            status_code=202,
            content={
                "status": "processing",
                "message": "SOAP note is being generated. Please check back shortly.",
                "consultation_id": str(consultation_id),
            }
        )

    soap_note = getattr(consultation, 'soap_note', None)
    if not soap_note:
        raise HTTPException(
            status_code=404,
            detail=(
                f"SOAP note not yet available (ai_status='{ai_status}'). "
                "Trigger generation via POST /analyze first."
            )
        )

    return {
        "consultation_id": str(consultation_id),
        "status": consultation.status,       # consultation status (e.g. completed)
        "ai_status": ai_status,
        "transcript_available": bool(getattr(consultation, 'transcript', None)),
        "soap_note": soap_note,
    }

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

    # Execute aggregate queries sequentially to avoid session concurrency issues
    pending_result = await db.execute(pending_stmt)
    urgent_result = await db.execute(urgent_stmt)
    cleared_result = await db.execute(cleared_stmt)


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
    patient_id: Optional[UUID] = Query(None, description="Filter by a specific patient"),
    current_user: User = Depends(get_current_active_user),
    organization_id: UUID = Depends(get_organization_id),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    """
    List consultations with advanced filtering and pagination.
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
        patient_id=patient_id,
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
        metadata={"filters": {"status": status, "search": search, "page": page, "patient_id": str(patient_id) if patient_id else None}}
    )
    await db.commit()
    
    response_list = []
    for c in consultations:
        response_list.append(await _consultation_to_response(c))
        
    return ConsultationListResponse(
        consultations=response_list,
        total=total_count
    )
