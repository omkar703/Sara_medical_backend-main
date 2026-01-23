"""Permission Service - HIPAA-compliant access control for medical records"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.data_access_grant import DataAccessGrant
from app.models.appointment import Appointment


class PermissionService:
    """
    Centralized permission checking for doctor access to patient records.
    HIPAA Compliance: Explicit patient consent required for all access.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def check_doctor_access(self, doctor_id: UUID, patient_id: UUID) -> bool:
        """
        Check if a doctor has permission to access a patient's medical records.
        
        Permission is granted if:
        1. An active DataAccessGrant exists, OR
        2. An active (accepted/pending) appointment exists between them
        
        Args:
            doctor_id: UUID of the doctor
            patient_id: UUID of the patient
        
        Returns:
            True if access is granted, False otherwise
        """
        
        # Check for active DataAccessGrant
        grant_query = select(DataAccessGrant).where(
            and_(
                DataAccessGrant.doctor_id == doctor_id,
                DataAccessGrant.patient_id == patient_id,
                DataAccessGrant.is_active == True,
                or_(
                    DataAccessGrant.expires_at.is_(None),
                    DataAccessGrant.expires_at > datetime.utcnow()
                )
            )
        )
        
        grant_result = await self.db.execute(grant_query)
        grant = grant_result.scalars().first()
        
        if grant:
            return True
        
        # Check for active appointment
        appointment_query = select(Appointment).where(
            and_(
                Appointment.doctor_id == doctor_id,
                Appointment.patient_id == patient_id,
                Appointment.status.in_(["pending", "accepted"]),
                Appointment.requested_date > datetime.utcnow()  # Future appointment
            )
        )
        
        appointment_result = await self.db.execute(appointment_query)
        appointment = appointment_result.scalars().first()
        
        return appointment is not None
    
    async def create_access_grant(
        self,
        doctor_id: UUID,
        patient_id: UUID,
        appointment_id: Optional[UUID] = None,
        grant_reason: Optional[str] = None,
        expires_at: Optional[datetime] = None
    ) -> DataAccessGrant:
        """
        Create a new data access grant.
        
        Args:
            doctor_id: UUID of the doctor
            patient_id: UUID of the patient
            appointment_id: Optional linked appointment
            grant_reason: Reason for granting access
            expires_at: Optional expiration timestamp
        
        Returns:
            Created DataAccessGrant object
        """
        grant = DataAccessGrant(
            doctor_id=doctor_id,
            patient_id=patient_id,
            appointment_id=appointment_id,
            grant_reason=grant_reason or "Appointment-based access",
            expires_at=expires_at,
            is_active=True
        )
        
        self.db.add(grant)
        await self.db.flush()
        
        return grant
    
    async def revoke_access_grant(
        self,
        grant_id: UUID,
        revoked_reason: Optional[str] = None
    ) -> bool:
        """
        Revoke an existing access grant.
        
        Args:
            grant_id: UUID of the grant to revoke
            revoked_reason: Reason for revocation
        
        Returns:
            True if successful, False if grant not found
        """
        query = select(DataAccessGrant).where(DataAccessGrant.id == grant_id)
        result = await self.db.execute(query)
        grant = result.scalar_one_or_none()
        
        if not grant:
            return False
        
        grant.is_active = False
        grant.revoked_at = datetime.utcnow()
        grant.revoked_reason = revoked_reason
        
        await self.db.flush()
        return True
