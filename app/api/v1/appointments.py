
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
    
    return appointment

@router.get("/patient-appointments", response_model=List[AppointmentResponse])
async def get_patient_appointments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Patient views their own appointments.
    """
    query = select(Appointment).where(
        Appointment.patient_id == current_user.id
    ).order_by(Appointment.requested_date.desc())
    
    result = await db.execute(query)
    appointments = result.scalars().all()
    return appointments

@router.patch("/{appointment_id}/status", response_model=AppointmentResponse)
async def update_appointment_status(
    appointment_id: UUID,
    status_update: AppointmentStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Doctor accepts or declines an appointment.
    """
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

    # Generate Zoom Meeting
    try:
        topic = f"Consultation with {current_user.full_name}"
        # We try to decrypt doctor name for the topic if possible, but full_name is encrypted in DB
        from app.core.security import pii_encryption
        try:
            doctor_name = pii_encryption.decrypt(current_user.full_name)
            topic = f"Consultation with Dr. {doctor_name}"
        except:
            pass
            
        zoom_meeting = await zoom_service.create_meeting(
            topic=topic,
            start_time=approval_in.appointment_time.isoformat(),
            duration_minutes=30
        )
        
        appointment.meeting_id = str(zoom_meeting["id"])
        appointment.join_url = zoom_meeting["join_url"]
        appointment.start_url = zoom_meeting["start_url"]
        appointment.meeting_password = zoom_meeting.get("password")
        
    except Exception as e:
        print(f"Error creating Zoom meeting: {e}")
        # We might want to still approve but alert, but the spec says approve implies Zoom
        raise HTTPException(status_code=500, detail=f"Failed to generate Zoom meeting: {str(e)}")

    appointment.status = "accepted"
    appointment.requested_date = approval_in.appointment_time
    if approval_in.doctor_notes:
        appointment.doctor_notes = approval_in.doctor_notes
    appointment.updated_at = datetime.utcnow()
    
    # Sync appointment to calendar (update events with confirmed time and Zoom link)
    from app.services.calendar_service import CalendarService
    calendar_service = CalendarService(db)
    await calendar_service.sync_appointment_to_calendar(appointment, "update")
    
    await db.commit()
    await db.refresh(appointment)
    
    # Create Activity Log for approval
    from app.models.activity_log import ActivityLog
    activity = ActivityLog(
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        activity_type="Appointment Scheduled",
        description=f"Appointment confirmed for {appointment.requested_date.strftime('%Y-%m-%d %H:%M')}",
        status="completed",
        extra_data={"appointment_id": str(appointment.id), "zoom_link": appointment.join_url}
    )
    db.add(activity)
    await db.commit()
    
    return appointment
