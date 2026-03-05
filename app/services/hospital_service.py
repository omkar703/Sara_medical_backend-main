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

        # Query 2: Today's Appointments
        appointments_stmt = select(func.count()).select_from(
            select(Consultation).where(
                Consultation.organization_id == organization_id,
                Consultation.scheduled_at >= start_of_today,
                Consultation.scheduled_at <= end_of_today,
                Consultation.deleted_at.is_(None)
            ).subquery()
        )

        # Query 3: Recent Invitations (Activities)
        activities_stmt = select(Invitation).where(
            Invitation.organization_id == organization_id
        ).order_by(Invitation.created_at.desc()).limit(10)

        # Execute queries concurrently for performance
        doctors_result, appts_result, activities_result = await asyncio.gather(
            self.db.execute(doctors_stmt),
            self.db.execute(appointments_stmt),
            self.db.execute(activities_stmt)
        )

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

        # Execute both queries concurrently to halve the response time
        doctors_result, patients_result = await asyncio.gather(
            self.db.execute(doctors_stmt),
            self.db.execute(patients_stmt)
        )

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

        # Execute all 4 queries concurrently
        (
            active_res, 
            today_res, 
            pending_res, 
            table_res
        ) = await asyncio.gather(
            self.db.execute(active_patients_stmt),
            self.db.execute(patients_today_stmt),
            self.db.execute(pending_patients_stmt),
            self.db.execute(patients_table_stmt)
        )

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