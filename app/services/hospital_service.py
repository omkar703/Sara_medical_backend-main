from datetime import datetime, time, timezone, date
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, Invitation
from app.models.consultation import Consultation
from app.models.patient import Patient
from app.core.security import PIIEncryption
from sqlalchemy import select
from app.models.user import User
from app.models.health_metric import HealthMetric
from app.models.document import Document
from app.models.appointment import Appointment


class HospitalService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_dashboard_overview(self, organization_id: UUID) -> dict:
        # Define the time boundaries for "Today" in UTC
        now = datetime.now(timezone.utc)
        start_of_today = datetime.combine(now.date(), time.min).replace(tzinfo=timezone.utc)
        end_of_today = datetime.combine(now.date(), time.max).replace(tzinfo=timezone.utc)

        # Query 1: Total Doctors
        doctors_stmt = select(func.count()).select_from(
            select(User).where(
                User.organization_id == organization_id,
                User.role == "doctor",
                User.deleted_at.is_(None)
            ).subquery()
        )

        # Query 2: Today's Appointments (from Consultations)
        appointments_stmt = select(func.count()).select_from(
            select(Consultation).where(
                Consultation.organization_id == organization_id,
                Consultation.scheduled_at >= start_of_today,
                Consultation.scheduled_at <= end_of_today,
                Consultation.status != "cancelled",
                Consultation.deleted_at.is_(None)
            ).subquery()
        )

        # Query 3: Recent Invitations (Activities)
        activities_stmt = select(Invitation).where(
            Invitation.organization_id == organization_id
        ).order_by(Invitation.created_at.desc()).limit(10)

        # Query 4: Cleared Today (appointments transitioned from pending today)
        cleared_today_stmt = select(func.count()).select_from(
            select(Appointment).where(
                Appointment.hospital_id == organization_id,
                Appointment.status.in_(["accepted", "declined", "cancelled", "rejected"]),
                Appointment.updated_at >= start_of_today,
                Appointment.updated_at <= end_of_today
            ).subquery()
        )

        # Query 5: Average Wait Time (of currently pending)
        pending_wait_stmt = select(Appointment.created_at).where(
            Appointment.hospital_id == organization_id,
            Appointment.status == "pending_hospital_approval"
        )

        # Execute queries sequentially to avoid session concurrency issues
        doctors_result = await self.db.execute(doctors_stmt)
        appts_result = await self.db.execute(appointments_stmt)
        activities_result = await self.db.execute(activities_stmt)
        cleared_result = await self.db.execute(cleared_today_stmt)
        pending_wait_res = await self.db.execute(pending_wait_stmt)

        # Calculate Average Wait
        pending_times = pending_wait_res.scalars().all()
        wait_time_str = "0m"
        if pending_times:
            total_wait_seconds = sum((now - (t if t.tzinfo else t.replace(tzinfo=timezone.utc))).total_seconds() for t in pending_times)
            avg_seconds = total_wait_seconds / len(pending_times)
            if avg_seconds < 60:
                wait_time_str = f"{int(avg_seconds)}s"
            elif avg_seconds < 3600:
                wait_time_str = f"{int(avg_seconds / 60)}m"
            else:
                wait_time_str = f"{int(avg_seconds / 3600)}h {int((avg_seconds % 3600) / 60)}m"

        # Format recent activities
        recent_activities = []
        invitations = activities_result.scalars().all()
        for inv in invitations:
            recent_activities.append({
                "activityId": str(inv.id),
                "activityType": "staff_invitation",
                "subject": f"Invited {inv.email}",
                "status": inv.status,
                "timestamp": inv.created_at
            })

        return {
            "metrics": {
                "totalDoctors": doctors_result.scalar() or 0,
                "todayAppointments": appts_result.scalar() or 0,
                "clearedToday": cleared_result.scalar() or 0,
                "avgWaitTime": wait_time_str
            },
            "recentActivities": recent_activities
        }
        
    async def get_appointments_overview(self, organization_id: UUID) -> dict:
        """
        Get overview metrics for appointments including:
        - Total scheduled appointments
        - Total accepted appointments
        - Transcriptions in queue (AI processing pending)
        - Pending notes (consultations needing doctor notes/SOAP)
        """
        from app.models.ai_processing_queue import AIProcessingQueue
        
        # Query 1: Count scheduled appointments
        scheduled_stmt = select(func.count()).select_from(
            select(Consultation).where(
                Consultation.organization_id == organization_id,
                Consultation.status == "scheduled",
                Consultation.deleted_at.is_(None)
            ).subquery()
        )
        
        # Query 2: Count accepted appointments
        accepted_stmt = select(func.count()).select_from(
            select(Consultation).where(
                Consultation.organization_id == organization_id,
                Consultation.status == "completed",
                Consultation.deleted_at.is_(None)
            ).subquery()
        )
        
        # Query 3: Count transcriptions in queue (pending or processing AI requests)
        transcriptions_stmt = select(func.count()).select_from(
            select(AIProcessingQueue).where(
                AIProcessingQueue.organization_id == organization_id,
                AIProcessingQueue.status.in_(["pending", "processing"]),
                AIProcessingQueue.request_type == "transcription"
            ).subquery()
        )
        
        # Query 4: Count pending notes (completed consultations with visit_state needing review)
        pending_notes_stmt = select(func.count()).select_from(
            select(Consultation).where(
                Consultation.organization_id == organization_id,
                Consultation.status == "completed",
                Consultation.visit_state.in_(["Needs Review", "Draft Ready"]),
                Consultation.deleted_at.is_(None)
            ).subquery()
        )
        
        # Execute queries sequentially to avoid session concurrency issues
        scheduled_result = await self.db.execute(scheduled_stmt)
        accepted_result = await self.db.execute(accepted_stmt)
        transcriptions_result = await self.db.execute(transcriptions_stmt)
        pending_notes_result = await self.db.execute(pending_notes_stmt)
        
        # Extract values
        scheduled_count = scheduled_result.scalar() or 0
        accepted_count = accepted_result.scalar() or 0
        transcriptions_count = transcriptions_result.scalar() or 0
        pending_notes_count = pending_notes_result.scalar() or 0
        
        return {
            "metrics": {
                "scheduledAppointments": scheduled_count,
                "acceptedAppointments": accepted_count,
                "transcriptionsInQueue": transcriptions_count,
                "pendingNotes": pending_notes_count
            }
        }
        
    async def get_hospital_directory(self, organization_id: UUID) -> dict:
        pii_encryption = PIIEncryption()
        
        # Query 1: Fetch all active doctors CREATED by this hospital organization
        doctors_stmt = select(User).where(
            User.organization_id == organization_id,
            User.role == "doctor",
            User.deleted_at.is_(None)
        ).order_by(User.created_at.desc())

        # Query 2: Fetch all active patients onboarded through this hospital's organization.
        # This covers both:
        #   (a) Patients directly onboarded by the hospital admin (created_by = hospital user)
        #   (b) Patients onboarded by doctors belonging to this hospital (same organization_id)
        # The organization_id on Patient is always set to the creator's org at onboarding time.
        patients_stmt = select(Patient).where(
            Patient.organization_id == organization_id,
            Patient.deleted_at.is_(None)
        ).order_by(Patient.created_at.desc())

        # Execute both queries sequentially to avoid session concurrency issues
        doctors_result = await self.db.execute(doctors_stmt)
        patients_result = await self.db.execute(patients_stmt)


        doctors_data = doctors_result.scalars().all()
        patients_data = patients_result.scalars().all()

        # Process Doctors
        doctors_list = []
        for doc in doctors_data:
            # Safely decrypt Name
            try:
                name = pii_encryption.decrypt(doc.full_name) if doc.full_name else "Unknown Doctor"
            except Exception:
                name = doc.full_name or "Unknown Doctor"

            # Safely decrypt Phone
            try:
                phone = pii_encryption.decrypt(doc.phone_number) if doc.phone_number else None
            except Exception:
                phone = doc.phone_number

            # Generate avatar preview URL if available
            avatar_preview = None
            if doc.avatar_url:
                try:
                    from app.services.minio_service import minio_service
                    from app.config import settings
                    avatar_preview = minio_service.generate_presigned_url(
                        bucket_name=settings.MINIO_BUCKET_AVATARS,
                        object_name=doc.avatar_url
                    )
                except Exception:
                    pass

            doctors_list.append({
                "id": str(doc.id),
                "name": name,
                "email": doc.email,
                "specialty": doc.specialty,
                "department": doc.department,
                "department_role": doc.department_role,
                "phone": phone,
                "avatar_url": avatar_preview,
                "joinedAt": doc.created_at
            })

        # Process Patients
        patients_list = []
        for pat in patients_data:
            # Safely decrypt Name
            try:
                name = pii_encryption.decrypt(pat.full_name) if pat.full_name else "Unknown Patient"
            except Exception:
                name = pat.full_name or "Unknown Patient"

            # Safely decrypt Date of Birth
            try:
                dob = pii_encryption.decrypt(pat.date_of_birth) if pat.date_of_birth else None
            except Exception:
                dob = pat.date_of_birth

            # Patient avatar logic: check linked user if possible
            avatar_preview = None
            if hasattr(pat, 'user') and pat.user and pat.user.avatar_url:
                try:
                    from app.services.minio_service import minio_service
                    from app.config import settings
                    avatar_preview = minio_service.generate_presigned_url(
                        bucket_name=settings.MINIO_BUCKET_AVATARS,
                        object_name=pat.user.avatar_url
                    )
                except Exception:
                    pass

            patients_list.append({
                "id": str(pat.id),
                "name": name,
                "mrn": pat.mrn,
                "gender": pat.gender,
                "dateOfBirth": dob,
                "avatar_url": avatar_preview,
                "joinedAt": pat.created_at
            })

        return {
            "doctors": doctors_list,
            "patients": patients_list
        }
        
    async def get_hospital_patients_overview(self, organization_id: UUID) -> dict:
        pii_encryption = PIIEncryption()
        
        # Define the time boundaries for "Today" in UTC
        now = datetime.now(timezone.utc)
        start_of_today = datetime.combine(now.date(), time.min).replace(tzinfo=timezone.utc)
        end_of_today = datetime.combine(now.date(), time.max).replace(tzinfo=timezone.utc)

        # 1. Count Active Patients (Total patients in the org)
        active_patients_stmt = select(func.count(Patient.id)).where(
            Patient.organization_id == organization_id,
            Patient.deleted_at.is_(None)
        )

        # 2. Count Patients Today (Distinct patients with completed consultations today)
        patients_today_stmt = select(func.count(func.distinct(Consultation.patient_id))).where(
            Consultation.organization_id == organization_id,
            Consultation.scheduled_at >= start_of_today,
            Consultation.scheduled_at <= end_of_today,
            Consultation.status == "completed",
            Consultation.deleted_at.is_(None)
        )

        # 3. Count Pending Patients (Distinct patients with scheduled/pending consultations today)
        pending_patients_stmt = select(func.count(func.distinct(Consultation.patient_id))).where(
            Consultation.organization_id == organization_id,
            Consultation.scheduled_at >= start_of_today,
            Consultation.scheduled_at <= end_of_today,
            Consultation.status.in_(["scheduled", "pending", "accepted"]),
            Consultation.deleted_at.is_(None)
        )

        # 4. Fetch Patients Table Data with Last Visit Subquery
        last_visit_subq = (
            select(
                Consultation.patient_id,
                func.max(Consultation.scheduled_at).label("last_visit")
            )
            .where(
                Consultation.organization_id == organization_id,
                Consultation.status == "completed",
                Consultation.deleted_at.is_(None)
            )
            .group_by(Consultation.patient_id)
            .subquery()
        )

        # Outer join the Patient table to the subquery.
        # Only show patients onboarded through this hospital's organization.
        patients_table_stmt = (
            select(Patient, last_visit_subq.c.last_visit)
            .outerjoin(last_visit_subq, Patient.id == last_visit_subq.c.patient_id)
            .where(
                Patient.organization_id == organization_id,
                Patient.deleted_at.is_(None)
            )
            .order_by(Patient.created_at.desc())
        )

        # Execute all 4 queries sequentially to avoid session concurrency issues
        active_res = await self.db.execute(active_patients_stmt)
        today_res = await self.db.execute(patients_today_stmt)
        pending_res = await self.db.execute(pending_patients_stmt)
        table_res = await self.db.execute(patients_table_stmt)


        # Extract metrics safely
        active_count = active_res.scalar() or 0
        today_count = today_res.scalar() or 0
        pending_count = pending_res.scalar() or 0

        # Process Table Rows
        patients_list = []
        for pat, last_visit_dt in table_res.all():
            
            # Safely decrypt Name
            try:
                name = pii_encryption.decrypt(pat.full_name) if pat.full_name else "Unknown Patient"
            except Exception:
                name = pat.full_name or "Unknown Patient"

            # Safely format Last Visit (with the requested try-except block)
            formatted_last_visit = None
            try:
                if last_visit_dt:
                    formatted_last_visit = last_visit_dt.isoformat()
            except Exception as e:
                # Fallback if the database returned a corrupted date or string format
                print(f"[Warning] Failed to format last_visit for patient {pat.id}: {e}")
                formatted_last_visit = str(last_visit_dt) if last_visit_dt else None

            # Generate avatar preview URL if available for patient (via linked user)
            avatar_preview = None
            if hasattr(pat, 'user') and pat.user and pat.user.avatar_url:
                try:
                    from app.services.minio_service import minio_service
                    from app.config import settings
                    avatar_preview = minio_service.generate_presigned_url(
                        bucket_name=settings.MINIO_BUCKET_AVATARS,
                        object_name=pat.user.avatar_url
                    )
                except Exception:
                    pass

            patients_list.append({
                "id": str(pat.id),
                "mrn": pat.mrn,
                "name": name,
                "gender": pat.gender,
                "avatar_url": avatar_preview,
                "lastVisit": formatted_last_visit
            })

        return {
            "metrics": {
                "activePatients": active_count,
                "patientsToday": today_count,
                "pendingPatients": pending_count
            },
            "patients": patients_list
        }
        
    async def get_hospital_staff(self, organization_id: UUID) -> dict:
        pii_encryption = PIIEncryption()

        # Query: Fetch all non-patient users (doctors, admins, hospital managers)
        # Only users belonging to this hospital's organization, explicitly excluding
        # patients and any soft-deleted accounts.
        staff_stmt = select(User).where(
            User.organization_id == organization_id,
            User.role.in_(["doctor", "hospital", "admin"]),
            User.deleted_at.is_(None)
        ).order_by(User.created_at.desc())

        result = await self.db.execute(staff_stmt)
        staff_data = result.scalars().all()

        total_staff = len(staff_data)
        staff_list = []

        for u in staff_data:
            # Safely decrypt Name
            try:
                name = pii_encryption.decrypt(u.full_name) if u.full_name else "Unknown Staff"
            except Exception:
                name = u.full_name or "Unknown Staff"

            # Safely decrypt Phone Number
            try:
                phone = pii_encryption.decrypt(u.phone_number) if u.phone_number else None
            except Exception:
                phone = u.phone_number

            # Determine Display Role
            # Uses 'department_role' if you add it in the future, otherwise capitalizes the system role
            display_role = getattr(u, 'department_role', None) or u.role.capitalize()
            
            # Determine Status
            display_status = getattr(u, 'staff_status', None) or "Active"

            # Generate avatar preview URL if available
            avatar_preview = None
            if u.avatar_url:
                try:
                    from app.services.minio_service import minio_service
                    from app.config import settings
                    avatar_preview = minio_service.generate_presigned_url(
                        bucket_name=settings.MINIO_BUCKET_AVATARS,
                        object_name=u.avatar_url
                    )
                except Exception:
                    pass

            staff_list.append({
                "id": str(u.id),
                "name": name,
                "role": display_role,
                "system_role": u.role, # Base role for reliable filtering (e.g., 'doctor')
                "specialty": u.specialty,
                "email": u.email,
                "phone": phone,
                "avatar_url": avatar_preview,
                "status": display_status
            })

        return {
            "metrics": {
                "totalStaff": total_staff
            },
            "staff": staff_list
        }
        
    async def get_patient_records(self, organization_id: UUID, patient_id: UUID) -> dict:
        """Fetch all health metrics and documents for a specific patient, including basic profile info."""
        
        from app.services.patient_service import PatientService
        patient_service = PatientService(self.db)
        
        # 1. Fetch and Decrypt Patient Profile
        result = await self.db.execute(
            select(Patient).where(
                Patient.id == patient_id,
                Patient.organization_id == organization_id,
                Patient.deleted_at.is_(None)
            )
        )
        patient = result.scalar_one_or_none()
        if not patient:
            raise ValueError("Patient not found or does not belong to this organization.")

        patient_info = patient_service.decrypt_patient_data(patient)

        # 2. Fetch Health Metrics (Vitals)
        metrics_stmt = select(HealthMetric).where(
            HealthMetric.patient_id == patient_id
        ).order_by(HealthMetric.recorded_at.desc())

        # 3. Fetch Documents
        docs_stmt = select(Document).where(
            Document.patient_id == patient_id,
            Document.deleted_at.is_(None)
        ).order_by(Document.uploaded_at.desc())

        # Execute queries sequentially
        metrics_result = await self.db.execute(metrics_stmt)
        docs_result = await self.db.execute(docs_stmt)

        metrics = metrics_result.scalars().all()
        docs = docs_result.scalars().all()

        # Format Metrics
        metrics_list = [{
            "id": str(m.id),
            "metric_type": m.metric_type,
            "value": m.value,
            "unit": m.unit,
            "recorded_at": m.recorded_at,
            "notes": m.notes
        } for m in metrics]

        # Format Documents
        docs_list = [{
            "id": str(d.id),
            "file_name": d.file_name,
            "file_type": d.file_type,
            "file_size": d.file_size,
            "category": d.category,
            "uploaded_at": d.uploaded_at,
            "status": "indexed" if d.total_chunks > 0 else "processing"
        } for d in docs]

        # Calculate Age
        age = "N/A"
        if patient_info.get("date_of_birth"):
            try:
                dob = patient_info["date_of_birth"]
                if isinstance(dob, str):
                    dob = date.fromisoformat(dob)
                today = date.today()
                age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            except Exception:
                pass

        return {
            "patient_info": {
                "id": str(patient_info["id"]),
                "full_name": patient_info["full_name"],
                "mrn": patient_info["mrn"],
                "gender": patient_info["gender"],
                "age": age,
                "date_of_birth": str(patient_info["date_of_birth"]),
                "phone_number": patient_info.get("phone_number"),
                "email": patient_info.get("email")
            },
            "health_metrics": metrics_list,
            "documents": docs_list
        }

    async def get_hospital_appointments(self, organization_id: UUID, status_filter: Optional[str] = None) -> list:
        """Fetch all appointments for the organization's doctors."""
        pii_encryption = PIIEncryption()
        
        # Fetch appointments where either the doctor belongs to the hospital OR the appointment was specifically routed to the hospital
        stmt = select(Appointment).join(User, Appointment.doctor_id == User.id, isouter=True).where(
            (User.organization_id == organization_id) | (Appointment.hospital_id == organization_id)
        )
        
        if status_filter:
            if status_filter == "pending":
                stmt = stmt.where(Appointment.status.in_(["pending", "pending_hospital_approval"]))
            else:
                stmt = stmt.where(Appointment.status == status_filter)
            
        stmt = stmt.order_by(Appointment.requested_date.desc())
        
        result = await self.db.execute(stmt)
        appointments = result.scalars().all()
        
        output = []
        for apt in appointments:
            output.append({
                "id": str(apt.id),
                "doctor_id": str(apt.doctor_id),
                "patient_id": str(apt.patient_id),
                "requested_date": apt.requested_date,
                "scheduled_at": apt.scheduled_at,
                "reason": apt.reason,
                "status": apt.status,
                "created_by": apt.created_by,
                "meet_link": apt.meet_link,
                "doctor_notes": apt.doctor_notes
            })
        return output

    async def manage_appointment(self, organization_id: UUID, appointment_id: UUID, action: str, **kwargs) -> dict:
        """Manage (accept, reschedule, cancel) an appointment for the organization."""
        stmt = select(Appointment).join(User, Appointment.doctor_id == User.id).where(
            Appointment.id == appointment_id,
            User.organization_id == organization_id
        )
        result = await self.db.execute(stmt)
        appointment = result.scalar_one_or_none()
        
        if not appointment:
            # Try to find by hospital_id if the join above failed or was too restrictive
            stmt = select(Appointment).where(
                Appointment.id == appointment_id,
                Appointment.hospital_id == organization_id
            )
            result = await self.db.execute(stmt)
            appointment = result.scalar_one_or_none()
            
        if not appointment:
            raise ValueError("Appointment not found in your organization.")
            
        from app.services.notification_service import NotificationService
        notification_service = NotificationService(self.db)

        if action == "approve":
            appointment.status = "accepted"
            if kwargs.get("scheduled_at"):
                appointment.scheduled_at = kwargs.get("scheduled_at")
            else:
                appointment.scheduled_at = appointment.requested_date
                
            appointment.approved_by_hospital = kwargs.get("approved_by")
            
            # Notify Doctor: "New appointment scheduled"
            await notification_service.create_notification(
                user_id=appointment.doctor_id,
                type="appointment_scheduled",
                title="New Appointment Scheduled",
                message=f"Hospital has approved and scheduled a new appointment with you for {appointment.scheduled_at.strftime('%Y-%m-%d %H:%M')}.",
                action_url=f"/appointments/{appointment.id}"
            )
            
            # Add to doctor's calendar
            from app.services.calendar_service import CalendarService
            calendar_service = CalendarService(self.db)
            await calendar_service.sync_appointment_to_calendar(appointment, "create")

        elif action == "decline":
            appointment.status = "declined"
            appointment.reschedule_note = kwargs.get("reschedule_note")
            
            # Notify Patient: "Please reschedule your appointment"
            await notification_service.create_notification(
                user_id=appointment.patient_id,
                type="appointment_declined",
                title="Appointment Request Declined",
                message=f"Your appointment request has been declined by the hospital. Note: {appointment.reschedule_note or 'Please reschedule'}",
                action_url=f"/appointments/request"
            )

        elif action == "accept":
            appointment.status = "accepted"
            if kwargs.get("scheduled_at"):
                appointment.scheduled_at = kwargs.get("scheduled_at")
            else:
                appointment.scheduled_at = appointment.requested_date
                
        elif action == "reschedule":
            new_date = kwargs.get("new_date")
            if not new_date:
                raise ValueError("New date is required for rescheduling.")
            appointment.requested_date = new_date
            appointment.scheduled_at = new_date
            appointment.status = "accepted"
            appointment.approved_by_hospital = kwargs.get("approved_by")
            
            # Notify Patient
            await notification_service.create_notification(
                user_id=appointment.patient_id,
                type="appointment_scheduled",
                title="Appointment Rescheduled",
                message=f"Your appointment request has been rescheduled and approved for {appointment.scheduled_at.strftime('%Y-%m-%d %H:%M')}.",
                action_url=f"/dashboard/patient/appointments"
            )
            
            # Notify Doctor & Sync Calendar (same as approve)
            await notification_service.create_notification(
                user_id=appointment.doctor_id,
                type="appointment_scheduled",
                title="Appointment Rescheduled",
                message=f"Hospital has rescheduled your appointment with the patient for {appointment.scheduled_at.strftime('%Y-%m-%d %H:%M')}.",
                action_url=f"/appointments/{appointment.id}"
            )
            from app.services.calendar_service import CalendarService
            calendar_service = CalendarService(self.db)
            await calendar_service.sync_appointment_to_calendar(appointment, "create")
            
        elif action == "cancel":
            appointment.status = "cancelled"
            
        if kwargs.get("notes"):
            appointment.doctor_notes = kwargs.get("notes")
            
        await self.db.commit()
        return {"id": str(appointment.id), "status": appointment.status}

    async def get_hospital_doctors(self, organization_id: UUID, department: Optional[str] = None) -> list:
        """Fetch all doctors for the organization, optionally filtered by department."""
        stmt = select(User).where(
            User.organization_id == organization_id,
            User.role == "doctor",
            User.deleted_at.is_(None)
        )
        
        if department:
            stmt = stmt.where(User.department == department)
            
        result = await self.db.execute(stmt)
        doctors = result.scalars().all()
        
        from app.core.security import pii_encryption
        from app.services.minio_service import minio_service
        from app.config import settings
        
        output = []
        for doc in doctors:
            try:
                full_name = pii_encryption.decrypt(doc.full_name)
            except:
                full_name = doc.full_name
                
            avatar_url = None
            if doc.avatar_url:
                try:
                    avatar_url = minio_service.generate_presigned_url(
                        bucket_name=settings.MINIO_BUCKET_AVATARS,
                        object_name=doc.avatar_url
                    )
                except: pass
                
            output.append({
                "id": str(doc.id),
                "name": full_name,
                "department": doc.department,
                "specialty": doc.specialty,
                "avatar_url": avatar_url,
                "is_active": doc.is_active
            })
        return output

    async def get_doctor_schedule(self, organization_id: UUID, doctor_id: UUID, start_date: datetime, end_date: datetime) -> dict:
        """Fetch a doctor's schedule including booked slots and availability."""
        # Verify doctor belongs to organization
        stmt = select(User).where(User.id == doctor_id, User.organization_id == organization_id)
        result = await self.db.execute(stmt)
        if not result.scalar_one_or_none():
            raise ValueError("Doctor not found in your organization.")
            
        # Fetch appointments in range
        stmt = select(Appointment).where(
            Appointment.doctor_id == doctor_id,
            Appointment.requested_date >= start_date,
            Appointment.requested_date <= end_date,
            Appointment.status != "cancelled"
        )
        result = await self.db.execute(stmt)
        appointments = result.scalars().all()
        
        # We can also fetch availability slots if we have an Availability model
        # For now, we return booked slots
        booked_slots = [{
            "id": str(apt.id),
            "start": apt.scheduled_at or apt.requested_date,
            "end": apt.scheduled_at or apt.requested_date, # Add duration logic if exists
            "status": apt.status,
            "title": "Booked"
        } for apt in appointments]
        
        return {
            "doctor_id": str(doctor_id),
            "booked_slots": booked_slots,
            "availability": [] # Place holder for availability patterns
        }