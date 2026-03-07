
from typing import List
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.appointment import Appointment
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentResponse,
    AppointmentStatusUpdate,
    AppointmentApproval
)
from app.services.zoom_service import zoom_service
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/appointments", tags=["Appointments"])

@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    appointment_in: AppointmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Patient creates an appointment request.
    Optionally grants doctor access to medical history.
    """
    appointment = Appointment(
        doctor_id=appointment_in.doctor_id,
        patient_id=current_user.id,
        requested_date=appointment_in.requested_date,
        reason=appointment_in.reason,
        status="pending"
    )
    
    db.add(appointment)
    await db.flush()
    
    # Create permission grant if requested
    if appointment_in.grant_access_to_history:
        from app.services.permission_service import PermissionService
        permission_service = PermissionService(db)
        await permission_service.create_access_grant(
            doctor_id=appointment_in.doctor_id,
            patient_id=current_user.id,
            appointment_id=appointment.id,
            grant_reason="Patient granted access during appointment booking"
        )
    
    # Sync appointment to calendar (create events for patient and doctor)
    from app.services.calendar_service import CalendarService
    calendar_service = CalendarService(db)
    await calendar_service.sync_appointment_to_calendar(appointment, "create")
    
    await db.commit()
    await db.refresh(appointment)
    
    # Notify Doctor
    notification_service = NotificationService(db)
    await notification_service.create_notification(
        user_id=appointment.doctor_id,
        type="appointment_requested",
        title="New Appointment Request",
        message=f"A patient has requested an appointment for {appointment.requested_date.strftime('%Y-%m-%d %H:%M')}.",
        action_url=f"/appointments/{appointment.id}"
    )
    
    return appointment

@router.get("/patient-appointments", response_model=List[AppointmentResponse])
async def get_patient_appointments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Patient views their own appointments.
    """
    from sqlalchemy.orm import selectinload
    from app.core.security import pii_encryption
    
    query = select(Appointment).options(
        selectinload(Appointment.doctor)
    ).where(
        Appointment.patient_id == current_user.id
    ).order_by(Appointment.requested_date.desc())
    
    result = await db.execute(query)
    appointments = result.scalars().all()
    
    response_list = []
    for appt in appointments:
        doc_name = "Unknown Doctor"
        if appt.doctor:
            try:
                doc_name = pii_encryption.decrypt(appt.doctor.full_name)
            except:
                doc_name = appt.doctor.full_name or "Unknown Doctor"
        
        # Pydantic will auto-map the rest, but we need to inject doctor_name
        response_dict = {
            "id": appt.id,
            "doctor_id": appt.doctor_id,
            "patient_id": appt.patient_id,
            "requested_date": appt.requested_date,
            "reason": appt.reason,
            "status": appt.status,
            "doctor_notes": appt.doctor_notes,
            "google_event_id": appt.google_event_id,
            "meet_link": appt.meet_link,
            "meeting_id": getattr(appt, 'meeting_id', None),
            "join_url": getattr(appt, 'join_url', None),
            "start_url": getattr(appt, 'start_url', None),
            "meeting_password": getattr(appt, 'meeting_password', None),
            "created_at": appt.created_at,
            "updated_at": appt.updated_at,
            "doctor_name": doc_name
        }
        response_list.append(AppointmentResponse(**response_dict))

    return response_list

@router.patch("/{appointment_id}/status", response_model=AppointmentResponse)
async def update_appointment_status(
    appointment_id: UUID,
    status_update: AppointmentStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Doctor updates appointment status (PATCH).
    """
    return await _do_update_appointment_status(appointment_id, status_update, db, current_user)


@router.put("/{appointment_id}/status", response_model=AppointmentResponse)
async def update_appointment_status_put(
    appointment_id: UUID,
    status_update: AppointmentStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Doctor updates appointment status (PUT - alias for PATCH).
    """
    return await _do_update_appointment_status(appointment_id, status_update, db, current_user)


async def _do_update_appointment_status(
    appointment_id: UUID,
    status_update: AppointmentStatusUpdate,
    db: AsyncSession,
    current_user: User
):
    """Shared logic for PATCH and PUT update_appointment_status"""
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can update appointment status")
    
    query = select(Appointment).where(
        Appointment.id == appointment_id,
        Appointment.doctor_id == current_user.id
    )
    result = await db.execute(query)
    appointment = result.scalar_one_or_none()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    appointment.status = status_update.status
    if status_update.doctor_notes:
        appointment.doctor_notes = status_update.doctor_notes
    appointment.updated_at = datetime.utcnow()
    
    # Sync appointment status to calendar
    from app.services.calendar_service import CalendarService
    calendar_service = CalendarService(db)
    
    # If declined or cancelled, mark calendar events as cancelled
    if status_update.status in ["declined", "cancelled"]:
        await calendar_service.sync_appointment_to_calendar(appointment, "cancel")
    else:
        await calendar_service.sync_appointment_to_calendar(appointment, "update")
    
    await db.commit()
    await db.refresh(appointment)
    
    # Notify Patient of cancellation/decline
    if status_update.status in ["declined", "cancelled"]:
        notification_service = NotificationService(db)
        await notification_service.create_notification(
            user_id=appointment.patient_id,
            type=f"appointment_{status_update.status}",
            title=f"Appointment {status_update.status.capitalize()}",
            message=f"Your appointment scheduled for {appointment.requested_date.strftime('%Y-%m-%d %H:%M')} has been {status_update.status}.",
            action_url=f"/appointments/{appointment.id}"
        )
    
    return appointment


@router.post("/{appointment_id}/approve", response_model=AppointmentResponse)
async def approve_appointment(
    appointment_id: UUID,
    approval_in: AppointmentApproval,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Doctor approves an appointment and generates a Zoom meeting.
    """
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can approve appointments")
    
    query = select(Appointment).where(
        Appointment.id == appointment_id,
        Appointment.doctor_id == current_user.id
    )
    result = await db.execute(query)
    appointment = result.scalar_one_or_none()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    if appointment.status != "pending":
        raise HTTPException(status_code=400, detail=f"Appointment is already {appointment.status}")

    # Generate Google Meet link using mock/real service
    from app.core.security import pii_encryption
    from app.services.mock_google_meet import google_meet_service as mock_meet_service
    from app.services.google_meet_service import google_meet_service as real_meet_service
    from app.config import settings

    try:
        doctor_name = pii_encryption.decrypt(current_user.full_name)
    except Exception:
        doctor_name = "Doctor"

    meeting_summary = f"Consultation with Dr. {doctor_name}"
    meet_link = None
    google_event_id = None

    # Determine which service to use
    use_real = settings.FEATURE_VIDEO_CALLS and getattr(real_meet_service, "_available", False)
    meet_service = real_meet_service if use_real else mock_meet_service
    
    print(f"[Appointments] Using {'REAL' if use_real else 'MOCK'} Google Meet service")
    
    try:
        google_event_id, meet_link = await meet_service.create_meeting(
            start_time=approval_in.appointment_time,
            duration_minutes=30,
            summary=meeting_summary,
            description="Medical consultation session",
            attendees=[current_user.email]
        )
        print(f"[Appointments] ✅ Meet link generated successfully via {'REAL' if use_real else 'MOCK'} service")
    except Exception as e:
        print(f"[Appointments] ❌ Meet service error ({type(e).__name__}): {e}")
        print(f"[Appointments] Falling back to generated stub link.")
        from uuid import uuid4
        u1 = uuid4().hex
        u2 = uuid4().hex
        google_event_id = str(uuid4())
        meet_link = f"https://meet.google.com/fallback-{u1[:4]}-{u2[:4]}"

    print(f"[Appointments] Generated meet_link: {meet_link}")

    # Store the meet link so both doctor & patient can join
    if not meet_link:
        print("[Appointments] ⚠ meet_link was None after service call. Generating immediate fallback.")
        from uuid import uuid4
        meet_link = f"https://meet.google.com/fallback-{uuid4().hex[:4]}-{uuid4().hex[:4]}"
        
    appointment.meet_link = meet_link
    appointment.google_event_id = google_event_id
    
    # Store legacy/alias fields too if they are being used by frontend
    # Note: These are NOT columns in the model, but we set them on the object 
    # for the session duration so the initial response is correct.
    appointment.join_url = meet_link
    appointment.start_url = meet_link

    appointment.status = "accepted"
    appointment.requested_date = approval_in.appointment_time
    if approval_in.doctor_notes:
        appointment.doctor_notes = approval_in.doctor_notes
    appointment.updated_at = datetime.utcnow()
    
    print(f"[Appointments] Appointment {appointment.id} updated to ACCEPTED with link {appointment.meet_link}")
    
    # Sync appointment to calendar (update events with confirmed time and Zoom link)
    from app.services.calendar_service import CalendarService
    calendar_service = CalendarService(db)
    await calendar_service.sync_appointment_to_calendar(appointment, "update")
    
    await db.commit()
    await db.refresh(appointment)
    
    # Store join_url locally to use after refresh
    final_link = appointment.meet_link
    
    # ── Create a linked Consultation record ───────────────────────────────
    # This enables SOAP note generation via the /consultations/{id}/complete endpoint
    consultation_id = None
    try:
        from app.models.consultation import Consultation
        linked_consultation = Consultation(
            doctor_id=current_user.id,
            patient_id=appointment.patient_id,
            organization_id=current_user.organization_id,
            scheduled_at=appointment.requested_date,
            duration_minutes=30,
            status="scheduled",
            google_event_id=google_event_id,
            meet_link=final_link,
            notes=appointment.doctor_notes,
            chief_complaint=appointment.reason,
        )
        db.add(linked_consultation)
        await db.commit()
        await db.refresh(linked_consultation)
        consultation_id = str(linked_consultation.id)
        print(f"[Appointments] ✅ Created linked consultation {consultation_id} for appointment {appointment.id}")
    except Exception as e:
        print(f"[Appointments] ⚠ Could not create linked consultation: {e}")
        # Non-fatal — appointment is still approved
    # ─────────────────────────────────────────────────────────────────────

    # Notify Patient of approval
    notification_service = NotificationService(db)
    await notification_service.create_notification(
        user_id=appointment.patient_id,
        type="appointment_approved",
        title="Appointment Approved",
        message=f"Your appointment has been approved for {appointment.requested_date.strftime('%Y-%m-%d %H:%M')}. Join meeting: {final_link}",
        action_url=f"/appointments/{appointment.id}"
    )
    
    # Create Activity Log for approval
    from app.models.activity_log import ActivityLog
    activity = ActivityLog(
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        activity_type="Appointment Scheduled",
        description=f"Appointment confirmed for {appointment.requested_date.strftime('%Y-%m-%d %H:%M')}",
        status="completed",
        extra_data={"appointment_id": str(appointment.id), "zoom_link": final_link, "consultation_id": consultation_id}
    )
    db.add(activity)
    await db.commit()
    
    # Return as dict to ensure all fields are included correctly
    response_dict = {
        "id": appointment.id,
        "doctor_id": appointment.doctor_id,
        "patient_id": appointment.patient_id,
        "requested_date": appointment.requested_date,
        "reason": appointment.reason,
        "status": appointment.status,
        "doctor_notes": appointment.doctor_notes,
        "google_event_id": appointment.google_event_id,
        "meet_link": final_link,
        "join_url": final_link,
        "start_url": final_link,
        "meeting_id": consultation_id,  # Use consultation_id as the meeting_id so frontend can route to SOAP page
        "created_at": appointment.created_at,
        "updated_at": appointment.updated_at,
        "doctor_name": doctor_name
    }
    
    return AppointmentResponse(**response_dict)


@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a single appointment by its ID.
    Accessible if current user is the doctor or patient of the appointment.
    """
    from sqlalchemy.orm import selectinload
    from app.core.security import pii_encryption
    
    query = select(Appointment).options(
        selectinload(Appointment.doctor)
    ).where(Appointment.id == appointment_id)
    
    result = await db.execute(query)
    appointment = result.scalar_one_or_none()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
        
    if current_user.id not in [appointment.patient_id, appointment.doctor_id] and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to view this appointment")

    doc_name = "Unknown Doctor"
    if appointment.doctor:
        try:
            doc_name = pii_encryption.decrypt(appointment.doctor.full_name)
        except Exception:
            doc_name = appointment.doctor.full_name or "Unknown Doctor"
            
    # Reload the object to ensure DB state
    await db.refresh(appointment)
    
    # Return as dict to ensure all temporary fields (start_url/join_url) 
    # and decrypted doctor name are included correctly.
    response_dict = {
        "id": appointment.id,
        "doctor_id": appointment.doctor_id,
        "patient_id": appointment.patient_id,
        "requested_date": appointment.requested_date,
        "reason": appointment.reason,
        "status": appointment.status,
        "doctor_notes": appointment.doctor_notes,
        "google_event_id": appointment.google_event_id,
        "meet_link": appointment.meet_link,
        "meeting_id": getattr(appointment, 'meeting_id', None),
        "join_url": getattr(appointment, 'join_url', None),
        "start_url": getattr(appointment, 'start_url', None),
        "meeting_password": getattr(appointment, 'meeting_password', None),
        "created_at": appointment.created_at,
        "updated_at": appointment.updated_at,
        "doctor_name": doc_name
    }
    return AppointmentResponse(**response_dict)


@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_appointment(
    appointment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cancel/delete an appointment.
    Accessible if current user is the doctor or patient of the appointment.
    """
    query = select(Appointment).where(Appointment.id == appointment_id)
    result = await db.execute(query)
    appointment = result.scalar_one_or_none()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
        
    if current_user.id not in [appointment.patient_id, appointment.doctor_id] and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to delete this appointment")

    # Sync to calendar (cancel)
    from app.services.calendar_service import CalendarService
    calendar_service = CalendarService(db)
    await calendar_service.sync_appointment_to_calendar(appointment, "cancel")
    
    await db.delete(appointment)
    await db.commit()
    
    return None
