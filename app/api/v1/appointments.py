from typing import List
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User
from app.models.appointment import Appointment
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentResponse,
    AppointmentStatusUpdate,
    AppointmentApproval,
    DoctorAppointmentCreate
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
    try:
        # Check if this is a hospital patient flow
        # A hospital patient is one who belongs to an organization that is not the 'default' one
        # For now, we assume if they have an organization_id, it's their hospital
        # In a real scenario, we might have a flag on the organization or check organization status
        
        status = "pending"
        hospital_id = None
        
        # Heuristic: If patient's record was 'created_by' a hospital admin OR belongs to an org WITH hospital users,
        # it's a hospital-mediated flow.
        from app.models.patient import Patient
        p_stmt = select(Patient).where(Patient.id == current_user.id)
        p_res = await db.execute(p_stmt)
        patient_record = p_res.scalar_one_or_none()
        
        is_hospital_flow = False
        if patient_record and patient_record.organization_id:
             # Check if there is an active 'hospital' role user in this organization
             h_user_stmt = select(User).where(
                 User.organization_id == patient_record.organization_id,
                 User.role == "hospital",
                 User.deleted_at.is_(None)
             )
             h_user_res = await db.execute(h_user_stmt)
             if h_user_res.scalars().first():
                 is_hospital_flow = True

        if is_hospital_flow:
             status = "pending_hospital_approval"
             hospital_id = patient_record.organization_id

        appointment = Appointment(
            doctor_id=appointment_in.doctor_id,
            patient_id=current_user.id,
            hospital_id=hospital_id,
            requested_date=appointment_in.requested_date,
            reason=appointment_in.reason,
            status=status
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
        
        await db.commit()
        
        # Sync appointment to calendar only if accepted (usually patient creates pending)
        if appointment.status == "accepted":
            from app.services.calendar_service import CalendarService
            calendar_service = CalendarService(db)
            await calendar_service.sync_appointment_to_calendar(appointment, "create")
        
        # Eagerly load relationships to avoid lazy loading issues in async
        stmt = select(Appointment).where(Appointment.id == appointment.id).options(
            selectinload(Appointment.doctor),
            selectinload(Appointment.patient)
        )
        result = await db.execute(stmt)
        appointment = result.scalars().unique().one_or_none()
        
        # Decrypt names and generate avatars for a full response
        from app.core.security import pii_encryption
        from app.services.minio_service import minio_service
        from app.config import settings
        
        doctor_name = "Unknown Doctor"
        if appointment.doctor:
            try:
                doctor_name = pii_encryption.decrypt(appointment.doctor.full_name)
            except:
                doctor_name = appointment.doctor.full_name or "Unknown Doctor"
                
        patient_name = "Unknown Patient"
        if current_user:
            try:
                patient_name = pii_encryption.decrypt(current_user.full_name)
            except:
                patient_name = current_user.full_name or "Unknown Patient"

        doctor_avatar = None
        if appointment.doctor and appointment.doctor.avatar_url:
            try:
                doctor_avatar = minio_service.generate_presigned_url(
                    bucket_name=settings.MINIO_BUCKET_AVATARS,
                    object_name=appointment.doctor.avatar_url
                )
            except: pass

        patient_avatar = None
        if current_user and current_user.avatar_url:
            try:
                patient_avatar = minio_service.generate_presigned_url(
                    bucket_name=settings.MINIO_BUCKET_AVATARS,
                    object_name=current_user.avatar_url
                )
            except: pass

        # Notify appropriate person
        notification_service = NotificationService(db)
        
        if appointment.status == "pending_hospital_approval":
            # Find the hospital admin user for this organization
            h_stmt = select(User).where(
                User.organization_id == appointment.hospital_id,
                User.role == "hospital",
                User.deleted_at.is_(None)
            )
            h_result = await db.execute(h_stmt)
            hospital_admin = h_result.scalars().first() # Use first() to avoid scalar_one errors
            
            if hospital_admin:
                await notification_service.create_notification(
                    user_id=hospital_admin.id,
                    type="appointment_routed_to_hospital",
                    title="New Patient Request",
                    message=f"A patient has requested an appointment which requires your approval for {appointment.requested_date.strftime('%Y-%m-%d %H:%M')}.",
                    action_url=f"/dashboard/hospital/approval-queue"
                )
        else:
            # Notify Doctor directly for regular appointments
            await notification_service.create_notification(
                user_id=appointment.doctor_id,
                type="appointment_requested",
                title="New Appointment Request",
                message=f"A patient has requested an appointment for {appointment.requested_date.strftime('%Y-%m-%d %H:%M')}.",
                action_url=f"/appointments/{appointment.id}"
            )
        
        # Construct response dictionary
        response_dict = {
            "id": appointment.id,
            "doctor_id": appointment.doctor_id,
            "patient_id": appointment.patient_id,
            "requested_date": appointment.requested_date,
            "reason": appointment.reason,
            "status": appointment.status,
            "doctor_name": doctor_name,
            "patient_name": patient_name,
            "doctor_avatar": doctor_avatar,
            "patient_avatar": patient_avatar,
            "created_by": getattr(appointment, 'created_by', 'patient'),
            "created_at": appointment.created_at,
            "updated_at": appointment.updated_at
        }
        
        return AppointmentResponse(**response_dict)
    except Exception as e:
        import traceback
        print(f"CRITICAL ERROR in create_appointment: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/doctor-create", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment_by_doctor(
    appointment_in: DoctorAppointmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["doctor"]))
):
    """
    Doctor creates an appointment request for a patient.
    Status is set to pending, patient must accept/reject.
    """
    appointment = Appointment(
        doctor_id=current_user.id,
        patient_id=appointment_in.patient_id,
        requested_date=appointment_in.requested_date,
        reason=appointment_in.reason,
        status="pending",
        created_by="doctor"
    )
    
    db.add(appointment)
    await db.flush()
    
    # Sync appointment to calendar
    from app.services.calendar_service import CalendarService
    calendar_service = CalendarService(db)
    await calendar_service.sync_appointment_to_calendar(appointment, "create")
    
    await db.commit()
    
    # Eagerly load relationships
    stmt = select(Appointment).where(Appointment.id == appointment.id).options(
        selectinload(Appointment.doctor),
        selectinload(Appointment.patient)
    )
    result = await db.execute(stmt)
    appointment = result.scalars().unique().one_or_none()
    
    # Decrypt names
    from app.core.security import pii_encryption
    doctor_name = "Unknown Doctor"
    if current_user:
        try:
            doctor_name = pii_encryption.decrypt(current_user.full_name)
        except:
            doctor_name = current_user.full_name or "Unknown Doctor"
            
    patient_name = "Unknown Patient"
    if appointment.patient:
        try:
            patient_name = pii_encryption.decrypt(appointment.patient.full_name)
        except:
            patient_name = appointment.patient.full_name or "Unknown Patient"

    # Notify Patient
    from app.services.notification_service import NotificationService
    notification_service = NotificationService(db)
    await notification_service.create_notification(
        user_id=appointment.patient_id,
        type="appointment_requested",
        title="New Appointment Request from Doctor",
        message=f"Dr. {doctor_name} has requested an appointment for {appointment.requested_date.strftime('%Y-%m-%d %H:%M')}.",
        action_url=f"/appointments/{appointment.id}"
    )
    
    response_dict = {
        "id": appointment.id,
        "doctor_id": appointment.doctor_id,
        "patient_id": appointment.patient_id,
        "requested_date": appointment.requested_date,
        "reason": appointment.reason,
        "status": appointment.status,
        "created_by": appointment.created_by,
        "doctor_name": doctor_name,
        "patient_name": patient_name,
        "created_at": appointment.created_at,
        "updated_at": appointment.updated_at
    }
    
    return AppointmentResponse(**response_dict)

@router.get("/patient-appointments", response_model=List[AppointmentResponse])
async def get_patient_appointments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["patient", "hospital", "admin"]))
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

    # Build doctor_id -> User lookup for avatars
    from app.models.user import User as UserModel
    doctor_ids = list({appt.doctor_id for appt in appointments if appt.doctor_id})
    doctor_user_map = {}
    if doctor_ids:
        du_result = await db.execute(select(UserModel).where(UserModel.id.in_(doctor_ids)))
        for u in du_result.scalars().all():
            doctor_user_map[u.id] = u

    response_list = []
    for appt in appointments:
        doc_name = "Unknown Doctor"
        if appt.doctor:
            try:
                doc_name = pii_encryption.decrypt(appt.doctor.full_name)
            except:
                doc_name = appt.doctor.full_name or "Unknown Doctor"

        # Generate doctor avatar presigned URL
        doctor_avatar = None
        doctor_user = doctor_user_map.get(appt.doctor_id)
        if doctor_user and doctor_user.avatar_url:
            from app.services.minio_service import minio_service
            from app.config import settings
            try:
                doctor_avatar = minio_service.generate_presigned_url(
                    bucket_name=settings.MINIO_BUCKET_AVATARS,
                    object_name=doctor_user.avatar_url
                )
            except Exception as e:
                print(f"Error generating doctor avatar URL for {appt.doctor_id}: {e}")

        # Pydantic will auto-map the rest, but we need to inject doctor_name
        response_dict = {
            "id": appt.id,
            "doctor_id": appt.doctor_id,
            "patient_id": appt.patient_id,
            "requested_date": appt.requested_date,
            "reason": appt.reason,
            "status": appt.status,
            "created_by": appt.created_by,
            "doctor_notes": appt.doctor_notes,
            "google_event_id": appt.google_event_id,
            "meet_link": appt.meet_link,
            "meeting_id": getattr(appt, 'meeting_id', None),
            "join_url": getattr(appt, 'join_url', None),
            "start_url": getattr(appt, 'start_url', None),
            "meeting_password": getattr(appt, 'meeting_password', None),
            "created_at": appt.created_at,
            "updated_at": appt.updated_at,
            "doctor_name": doc_name,
            "doctor_avatar": doctor_avatar
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
    Update appointment status (PUT - alias for PATCH).
    Can be used by Patient to accept/decline doctor-created appointments.
    """
    return await _do_update_appointment_status(appointment_id, status_update, db, current_user)


async def _do_update_appointment_status(
    appointment_id: UUID,
    status_update: AppointmentStatusUpdate,
    db: AsyncSession,
    current_user: User
):
    """Shared logic for PATCH and PUT update_appointment_status"""
    
    query = select(Appointment).options(
        selectinload(Appointment.doctor),
        selectinload(Appointment.patient)
    ).where(Appointment.id == appointment_id)
    result = await db.execute(query)
    appointment = result.scalar_one_or_none()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    # Authorize
    is_doctor = current_user.role == "doctor" and appointment.doctor_id == current_user.id
    is_patient = current_user.role == "patient" and appointment.patient_id == current_user.id
    
    if not (is_doctor or is_patient):
        raise HTTPException(status_code=403, detail="Not authorized to update this appointment")
    
    # Check if patient is trying to accept/decline a doctor-created appointment
    if is_patient and appointment.created_by != "doctor":
        if status_update.status in ["accepted", "completed"]:
            raise HTTPException(status_code=403, detail="Patients cannot accept their own requests.")
    
    appointment.status = status_update.status
    if status_update.doctor_notes:
        appointment.doctor_notes = status_update.doctor_notes
    if status_update.reschedule_note:
        appointment.reschedule_note = status_update.reschedule_note
    appointment.updated_at = datetime.utcnow()
    
    # Special handling for when an appointment becomes 'accepted'
    if appointment.status == "accepted":
        # Generate Google Meet link if not exists
        if not appointment.meet_link:
            from app.services.google_meet_service import google_meet_service
            from app.core.security import pii_encryption
            
            p_name = "Patient"
            d_name = "Doctor"
            # Decrypt names for Meet summary
            try:
                if appointment.patient:
                    p_name = pii_encryption.decrypt(appointment.patient.full_name)
            except:
                pass
            try:
                if appointment.doctor:
                    d_name = pii_encryption.decrypt(appointment.doctor.full_name)
            except:
                pass
                
            summary = f"Consultation: Dr. {d_name} & {p_name}"
            # Fetch emails for attendees if possible
            attendees = []
            if appointment.patient.email:
                attendees.append(appointment.patient.email)
            if appointment.doctor.email:
                attendees.append(appointment.doctor.email)
                
            try:
                g_event_id, meet_link = await google_meet_service.create_meeting(
                    start_time=appointment.requested_date,
                    duration_minutes=30,
                    summary=summary,
                    attendees=attendees
                )
                appointment.google_event_id = g_event_id
                appointment.meet_link = meet_link
            except Exception as e:
                print(f"Failed to create Google Meet: {e}")

    # Sync appointment status to calendar
    from app.services.calendar_service import CalendarService
    calendar_service = CalendarService(db)
    
    # If declined/rejected/cancelled, remove calendar events
    if status_update.status in ["declined", "cancelled", "rejected"]:
        await calendar_service.sync_appointment_to_calendar(appointment, "cancel")
    else:
        # If it was pending and now accepted, 'update' in calendar_service 
        # will handle creation if events don't exist yet (thanks to our recent change)
        await calendar_service.sync_appointment_to_calendar(appointment, "update")
    
    await db.commit()
    await db.refresh(appointment)
    
    notification_service = NotificationService(db)
    
    # Patient accepted/rejected a doctor-created appointment → notify doctor
    if is_patient and appointment.created_by == "doctor":
        if status_update.status == "accepted":
            await notification_service.create_notification(
                user_id=appointment.doctor_id,
                type="appointment_accepted",
                title="Appointment Accepted",
                message=f"A patient has accepted your appointment request for {appointment.requested_date.strftime('%Y-%m-%d %H:%M')}.",
                action_url=f"/appointments/{appointment.id}"
            )
        elif status_update.status in ["rejected", "declined"]:
            await notification_service.create_notification(
                user_id=appointment.doctor_id,
                type="appointment_rejected",
                title="Appointment Declined",
                message=f"A patient has declined your appointment request for {appointment.requested_date.strftime('%Y-%m-%d %H:%M')}.",
                action_url=f"/appointments/{appointment.id}"
            )
    
    # Doctor declined/cancelled a patient-created appointment → notify patient
    elif is_doctor and status_update.status in ["declined", "cancelled"]:
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

    # Generate real Google Meet link
    from app.core.security import pii_encryption
    from app.services.google_meet_service import google_meet_service as real_meet_service

    try:
        doctor_name = pii_encryption.decrypt(current_user.full_name)
    except Exception:
        doctor_name = "Doctor"

    meeting_summary = f"Consultation with Dr. {doctor_name}"
    
    try:
        print(f"[Appointments] Generating real Google Meet link...")
        google_event_id, meet_link = await real_meet_service.create_meeting(
            start_time=approval_in.appointment_time,
            duration_minutes=30,
            summary=meeting_summary,
            description="Medical consultation session",
            attendees=[current_user.email]
        )
        print(f"[Appointments] ✅ Real Google Meet link generated successfully: {meet_link}")
    except Exception as e:
        print(f"[Appointments] ❌ Google Meet service error ({type(e).__name__}): {e}")
        print(f"[Appointments] Ensure Google credentials are configured in .env:")
        print(f"[Appointments]   - GOOGLE_CLIENT_ID")
        print(f"[Appointments]   - GOOGLE_CLIENT_SECRET")
        print(f"[Appointments]   - GOOGLE_REFRESH_TOKEN")
        raise
        
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
        "created_by": appointment.created_by,
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
        "created_by": appointment.created_by,
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
