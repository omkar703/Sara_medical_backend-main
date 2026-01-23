"""Consultation Service"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.consultation import Consultation
from app.models.patient import Patient
from app.models.user import User
from app.services.zoom_service import ZoomService


class ConsultationService:
    """Service for consultation business logic"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.zoom = ZoomService()
        
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

        # 2. Create Zoom Meeting
        meeting_topic = f"Consultation: Dr. {doctor.full_name} - {patient.mrn}"
        start_time_str = scheduled_at.isoformat().replace("+00:00", "Z")
        
        zoom_meeting = await self.zoom.create_meeting(
            topic=meeting_topic,
            start_time=start_time_str,
            duration_minutes=duration_minutes,
            agenda=f"Medical consultation for {patient.mrn}"
        )
        
        # 3. Create Database Record
        consultation = Consultation(
            doctor_id=doctor_id,
            patient_id=patient_id,
            organization_id=organization_id,
            scheduled_at=scheduled_at,
            duration_minutes=duration_minutes,
            status="scheduled",
            notes=notes,
            meeting_id=str(zoom_meeting.get("id")),
            join_url=zoom_meeting.get("join_url"),
            start_url=zoom_meeting.get("start_url"),
            password=zoom_meeting.get("password"),
            ai_status="pending"
        )
        
        self.db.add(consultation)
        await self.db.flush()
        
        # Refresh to load relationships for response
        await self.db.refresh(consultation, attribute_names=["doctor", "patient"])
        
        return consultation
    
    async def list_consultations(
        self,
        organization_id: UUID,
        user_id: UUID,
        role: str,
        status: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[Consultation]:
        """
        List consultations with filtering.
        Doctors/Admins see all for org (or filtered).
        Patients see only their own.
        """
        query = select(Consultation).options(
            selectinload(Consultation.doctor),
            selectinload(Consultation.patient)
        ).where(
            Consultation.organization_id == organization_id,
            Consultation.deleted_at.is_(None)
        )
        
        # Role-based filtering
        if role == "patient":
            # Patients typically don't log in directly to backend in this model, 
            # but if they did, filter by patient_id.
            # Assuming 'user_id' here might map to a patient record for patient portal users
            pass 
        elif role == "doctor":
            # Doctors see their own appointments primarily
            query = query.where(Consultation.doctor_id == user_id)
        
        # Filters
        if status:
            query = query.where(Consultation.status == status)
        
        if date_from:
            query = query.where(Consultation.scheduled_at >= date_from)
            
        if date_to:
            query = query.where(Consultation.scheduled_at <= date_to)
            
        query = query.order_by(Consultation.scheduled_at.asc())
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
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
        
        for field, value in updates.items():
            if hasattr(consultation, field) and value is not None:
                setattr(consultation, field, value)
        
        await self.db.flush()
        return consultation
