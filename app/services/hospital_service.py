import asyncio
from datetime import datetime, time, timezone
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

        # Query 2: Today's Appointments (from CalendarEvents)
        from app.models.calendar_event import CalendarEvent
        
        appointments_stmt = select(func.count()).select_from(
            select(CalendarEvent).where(
                CalendarEvent.organization_id == organization_id,
                CalendarEvent.event_type == "appointment",
                CalendarEvent.start_time >= start_of_today,
                CalendarEvent.start_time <= end_of_today,
                CalendarEvent.status != "cancelled"
            ).subquery()
        )

        # Query 3: Recent Invitations (Activities)
        activities_stmt = select(Invitation).where(
            Invitation.organization_id == organization_id
        ).order_by(Invitation.created_at.desc()).limit(10)

        # Execute queries sequentially to avoid session concurrency issues
        doctors_result = await self.db.execute(doctors_stmt)
        appts_result = await self.db.execute(appointments_stmt)
        activities_result = await self.db.execute(activities_stmt)


        # Extract values
        total_doctors = doctors_result.scalar() or 0
        today_appointments = appts_result.scalar() or 0
        invitations = activities_result.scalars().all()

        # Format recent activities
        recent_activities = []
        for inv in invitations:
            recent_activities.append({
                "activityId": str(inv.id),
                "activityType": "staff_invitation",
                "subject": inv.email,
                "status": inv.status,
                "timestamp": inv.created_at
            })

        return {
            "metrics": {
                "totalDoctors": total_doctors,
                "todayAppointments": today_appointments
            },
            "recentActivities": recent_activities
        }
        
    async def get_hospital_directory(self, organization_id: UUID) -> dict:
        pii_encryption = PIIEncryption()
        
        # Query 1: Fetch all active doctors for this organization
        doctors_stmt = select(User).where(
            User.organization_id == organization_id,
            User.role == "doctor",
            User.deleted_at.is_(None)
        ).order_by(User.created_at.desc())

        # Query 2: Fetch all active patients for this organization
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

            doctors_list.append({
                "id": str(doc.id),
                "name": name,
                "email": doc.email,
                "specialty": doc.specialty,
                "department": doc.department,
                "department_role": doc.department_role,
                "phone": phone,
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

            patients_list.append({
                "id": str(pat.id),
                "name": name,
                "mrn": pat.mrn,
                "gender": pat.gender,
                "dateOfBirth": dob,
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

        # Outer join the Patient table to the subquery
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

            patients_list.append({
                "id": str(pat.id),
                "mrn": pat.mrn,
                "name": name,
                "gender": pat.gender,
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
        staff_stmt = select(User).where(
            User.organization_id == organization_id,
            User.role != "patient",
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

            staff_list.append({
                "id": str(u.id),
                "name": name,
                "role": display_role,
                "specialty": u.specialty,
                "email": u.email,
                "phone": phone,
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