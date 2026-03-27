"""Consultation Service"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, select, or_, func, String, cast
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.consultation import Consultation
from app.models.patient import Patient
from app.models.user import User
from app.services.google_meet_service import google_meet_service as real_google_meet_service
from app.config import settings
from app.core.security import pii_encryption
from app.models.recent_doctors import RecentDoctor  
from app.models.recent_patients import RecentPatient


class ConsultationService:
    """Service for consultation business logic"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def schedule_consultation(
        self,
        doctor_id: UUID,
        patient_id: UUID,
        organization_id: UUID,
        scheduled_at: datetime,
        duration_minutes: int,
        notes: Optional[str] = None
    ) -> Consultation:
        """
        Schedule a new consultation and create Zoom meeting
        """
        # 1. Fetch patient and doctor details for the meeting info
        patient_result = await self.db.execute(select(Patient).where(Patient.id == patient_id))
        patient = patient_result.scalar_one_or_none()
        
        doctor_result = await self.db.execute(select(User).where(User.id == doctor_id))
        doctor = doctor_result.scalar_one_or_none()
        
        if not patient or not doctor:
            raise ValueError("Patient or Doctor not found")

        # 2. Create Google Meet
        try:
            doc_name = pii_encryption.decrypt(doctor.full_name)
        except:
            doc_name = doctor.full_name or "Doctor"
            
        meeting_topic = f"Consultation: Dr. {doc_name} - {patient.mrn}"
        
        # Decrypt patient email (PII-encrypted in DB) for Calendar invite
        try:
            patient_email = pii_encryption.decrypt(patient.email) if patient.email else None
        except Exception:
            patient_email = None  # Graceful fallback — invite skipped for patient

        attendees = [doctor.email]  # Doctor email is plain text in User model
        if patient_email:
            attendees.append(patient_email)

        google_event_id, meet_link = None, None
        try:
            # Use real Google Meet service for consultation scheduling
            google_event_id, meet_link = await real_google_meet_service.create_meeting(
                start_time=scheduled_at,
                duration_minutes=duration_minutes,
                summary=meeting_topic,
                description=f"Medical consultation for {patient.mrn}",
                attendees=attendees
            )
            print(f"[Consultation Service] ✅ Real Google Meet link generated successfully")
        except Exception as e:
            print(f"[Consultation Service] ⚠ Real Google Meet service failed: {e}")
            print(f"[Consultation Service] Ensure Google credentials are configured in .env:")
            print(f"[Consultation Service]   - GOOGLE_CLIENT_ID")
            print(f"[Consultation Service]   - GOOGLE_CLIENT_SECRET")
            print(f"[Consultation Service]   - GOOGLE_REFRESH_TOKEN")
            raise
        
        print(f"[Consultation Service] Resulting meet_link: {meet_link}")

        
        # 3. Create Database Record (Using the new Google fields)
        consultation = Consultation(
            doctor_id=doctor_id,
            patient_id=patient_id,
            organization_id=organization_id,
            scheduled_at=scheduled_at,
            duration_minutes=duration_minutes,
            status="scheduled",
            notes=notes,
            google_event_id=google_event_id,
            meet_link=meet_link,
            ai_status="pending"
        )
        
        self.db.add(consultation)
        await self.db.flush()
        
        # 4. Notify Patient (if they have a user account)
        try:
            # Check if this patient ID exists in the users table (registered patients)
            # In our system, registered patients have User.id == Patient.id
            user_check = await self.db.execute(select(User.id).where(User.id == patient_id))
            if user_check.scalar_one_or_none():
                from app.services.notification_service import NotificationService
                notif_service = NotificationService(self.db)
                
                await notif_service.create_notification(
                    user_id=patient_id,
                    type="consultation_started",
                    title="Consultation Started",
                    message=f"Dr. {doc_name} has started a live consultation session. click here to join.",
                    organization_id=organization_id,
                    action_url=f"/dashboard/patient/video-call?consultationId={consultation.id}",
                    action_metadata={
                        "consultation_id": str(consultation.id),
                        "meet_link": meet_link,
                        "doctor_name": doc_name
                    }
                )
        except Exception as e:
            # Notifications are best-effort; don't break the consultation creation if it fails
            print(f"[Consultation Service] ⚠ Failed to send notification to patient {patient_id}: {e}")

        # 5. Update Recent History for both participants
        try:
            # Update Recent Patient for the Doctor
            rp_stmt = select(RecentPatient).where(
                RecentPatient.doctor_id == doctor_id,
                RecentPatient.patient_id == patient_id
            )
            rp_res = await self.db.execute(rp_stmt)
            recent_patient = rp_res.scalar_one_or_none()
            
            if recent_patient:
                recent_patient.last_visit_at = datetime.utcnow()
                recent_patient.visit_count += 1
            else:
                self.db.add(RecentPatient(
                    doctor_id=doctor_id,
                    patient_id=patient_id,
                    last_visit_at=datetime.utcnow(),
                    visit_count=1
                ))
            
            # Update Recent Doctor for the Patient
            rd_stmt = select(RecentDoctor).where(
                RecentDoctor.patient_id == patient_id,
                RecentDoctor.doctor_id == doctor_id
            )
            rd_res = await self.db.execute(rd_stmt)
            recent_doctor = rd_res.scalar_one_or_none()
            
            if recent_doctor:
                recent_doctor.last_visit_at = datetime.utcnow()
                recent_doctor.visit_count += 1
            else:
                self.db.add(RecentDoctor(
                    patient_id=patient_id,
                    doctor_id=doctor_id,
                    last_visit_at=datetime.utcnow(),
                    visit_count=1
                ))
            
            await self.db.flush()
        except Exception as e:
            print(f"[Consultation Service] ⚠ Failed to update recent history: {e}")

        # Refresh to load relationships for response
        await self.db.refresh(consultation, attribute_names=["doctor", "patient"])
        
        return consultation
    
    async def list_consultations(
        self,
        organization_id: UUID,
        user_id: UUID,
        role: str,
        status: Optional[str] = None,
        visit_state: Optional[str] = None,
        urgency_level: Optional[str] = None,
        provider_id: Optional[UUID] = None,
        patient_id: Optional[UUID] = None,
        search_query: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> tuple[List[Consultation], int]:
        """
        List consultations with advanced filtering for the Approval Queue.
        Returns a tuple of (List of Consultations, Total Count).
        """
        # Base query with eager loading to prevent N+1 issues when fetching rows
        query = select(Consultation).options(
            selectinload(Consultation.doctor),
            selectinload(Consultation.patient)
        ).where(
            Consultation.organization_id == organization_id,
            Consultation.deleted_at.is_(None)
        )
        
        # --- Apply Filters ---
        if role == "patient":
             # Patients only see their own
             query = query.where(Consultation.patient_id == user_id)
        elif role == "doctor" and not provider_id:
            # By default, doctors might only see their own
            query = query.where(Consultation.doctor_id == user_id)
        elif provider_id:
            query = query.where(Consultation.doctor_id == provider_id)

        # 2. Patient Specific Filter (High Priority)
        # If a specific patient_id is passed (e.g., from the Patient Directory details),
        # we MUST restrict results to that specific patient only.
        if patient_id:
            query = query.where(Consultation.patient_id == patient_id)

        if status:
            query = query.where(Consultation.status == status)
            
        if visit_state:
            query = query.where(Consultation.visit_state == visit_state)
            
        if urgency_level:
            query = query.where(Consultation.urgency_level == urgency_level)

        if search_query:
            search_term = f"%{search_query}%"
            # Join required for searching patient/doctor names
            query = query.join(Consultation.patient).join(Consultation.doctor).where(
                or_(
                    Patient.full_name.ilike(search_term),
                    Patient.mrn.ilike(search_term),
                    User.full_name.ilike(search_term),
                    # Cast UUID to text for searching Session IDs
                    cast(Consultation.id, String).ilike(search_term)
                )
            )

        if date_from:
            query = query.where(Consultation.scheduled_at >= date_from)
            
        if date_to:
            query = query.where(Consultation.scheduled_at <= date_to)

        # Calculate total count before pagination
        count_query = select(func.count()).select_from(query.subquery())
        total_count_result = await self.db.execute(count_query)
        total_count = total_count_result.scalar() or 0

        # Apply ordering and pagination
        query = query.order_by(Consultation.scheduled_at.desc()).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all(), total_count
    
    async def get_consultation(
        self,
        consultation_id: UUID,
        organization_id: UUID
    ) -> Optional[Consultation]:
        """Get single consultation details"""
        query = select(Consultation).options(
            selectinload(Consultation.doctor),
            selectinload(Consultation.patient)
        ).where(
            Consultation.id == consultation_id,
            Consultation.organization_id == organization_id,
            Consultation.deleted_at.is_(None)
        )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def _sync_recent_connections(self, consultation: Consultation):
        """
        Updates RecentDoctor and RecentPatient tables.
        Called when a consultation is marked 'completed'.
        """
        # 1. Update Doctor's Recent Patients List
        stmt_pat = select(RecentPatient).where(
            RecentPatient.doctor_id == consultation.doctor_id,
            RecentPatient.patient_id == consultation.patient_id
        )
        result_pat = await self.db.execute(stmt_pat)
        recent_pat = result_pat.scalars().first()

        if recent_pat:
            # Update existing
            recent_pat.last_visit_at = datetime.utcnow()
            recent_pat.visit_count += 1
        else:
            # Create new
            new_pat = RecentPatient(
                doctor_id=consultation.doctor_id,
                patient_id=consultation.patient_id,
                last_visit_at=datetime.utcnow(),
                visit_count=1
            )
            self.db.add(new_pat)

        # 2. Update Patient's Recent Doctors List
        stmt_doc = select(RecentDoctor).where(
            RecentDoctor.patient_id == consultation.patient_id,
            RecentDoctor.doctor_id == consultation.doctor_id
        )
        result_doc = await self.db.execute(stmt_doc)
        recent_doc = result_doc.scalars().first()

        if recent_doc:
            # Update existing
            recent_doc.last_visit_at = datetime.utcnow()
            recent_doc.visit_count += 1
        else:
            # Create new
            new_doc = RecentDoctor(
                patient_id=consultation.patient_id,
                doctor_id=consultation.doctor_id,
                last_visit_at=datetime.utcnow(),
                visit_count=1
            )
            self.db.add(new_doc)
            
        await self.db.flush()
    
    async def update_consultation(
        self,
        consultation_id: UUID,
        organization_id: UUID,
        updates: Dict
    ) -> Optional[Consultation]:
        """Update consultation status or notes"""
        consultation = await self.get_consultation(consultation_id, organization_id)
        if not consultation:
            return None
        
        # Check if status is changing to 'completed'
        is_completing = (
            updates.get("status") == "completed" and 
            consultation.status != "completed"
        )
        
        for field, value in updates.items():
            if hasattr(consultation, field) and value is not None:
                setattr(consultation, field, value)
        
        # Update completion time if finishing
        if is_completing:
            consultation.completion_time = datetime.utcnow()
            await self._sync_recent_connections(consultation)
            # We no longer trigger AI SOAP generation automatically here.
            # The doctor now triggers it manually from the SOAP page 
            # after the transcript is confirmed as 'Available'.
            # This ensures better data quality and follows the new workflow.
        
        await self.db.flush()
        return consultation
    