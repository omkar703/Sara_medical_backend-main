"""Permission Service - HIPAA-compliant access control for medical records"""

from datetime import datetime, timezone
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
        now = datetime.now(timezone.utc)
        
        # Check for active DataAccessGrant
        grant_query = select(DataAccessGrant).where(
            and_(
                DataAccessGrant.doctor_id == doctor_id,
                DataAccessGrant.patient_id == patient_id,
                DataAccessGrant.status == "active",
                DataAccessGrant.is_active == True,
                or_(
                    DataAccessGrant.expires_at.is_(None),
                    DataAccessGrant.expires_at > now
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
                Appointment.requested_date > now  # Future appointment
            )
        )
        
        appointment_result = await self.db.execute(appointment_query)
        appointment = appointment_result.scalars().first()
        
        return appointment is not None
    
    async def request_access(
        self,
        doctor_id: UUID,
        patient_id: UUID,
        reason: Optional[str] = None
    ) -> DataAccessGrant:
        """
        Doctor requests access to a patient's records.
        """
        # Check if already exists
        existing_query = select(DataAccessGrant).where(
            DataAccessGrant.doctor_id == doctor_id,
            DataAccessGrant.patient_id == patient_id,
            DataAccessGrant.is_active == True
        )
        existing = (await self.db.execute(existing_query)).scalars().first()
        
        if existing:
            if existing.status == "active":
                return existing # Already active
            # Update pending request
            existing.status = "pending"
            existing.grant_reason = reason
            existing.revoked_at = None
            return existing
            
        # Create new pending request
        grant = DataAccessGrant(
            doctor_id=doctor_id,
            patient_id=patient_id,
            grant_reason=reason or "Doctor requested access",
            status="pending", # Default is active in model, we set pending here
            is_active=True
        )
        self.db.add(grant)
        await self.db.flush()
        return grant

    async def create_access_grant(
        self,
        doctor_id: UUID,
        patient_id: UUID,
        appointment_id: Optional[UUID] = None,
        grant_reason: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        access_level: str = "read_analyze",
        ai_access_permission: bool = False
    ) -> DataAccessGrant:
        """
        Create (or Approve) a data access grant.
        """
        # Check for existing request/grant
        stmt = select(DataAccessGrant).where(
            DataAccessGrant.doctor_id == doctor_id,
            DataAccessGrant.patient_id == patient_id
        )
        result = await self.db.execute(stmt)
        existing_grant = result.scalars().first()
        
        if existing_grant:
            # Update existing
            existing_grant.status = "active"
            existing_grant.is_active = True
            existing_grant.grant_reason = grant_reason
            existing_grant.expires_at = expires_at
            existing_grant.access_level = access_level
            existing_grant.ai_access_permission = ai_access_permission
            existing_grant.revoked_at = None
            return existing_grant

        grant = DataAccessGrant(
            doctor_id=doctor_id,
            patient_id=patient_id,
            appointment_id=appointment_id,
            grant_reason=grant_reason or "Appointment-based access",
            expires_at=expires_at,
            is_active=True,
            status="active",
            access_level=access_level,
            ai_access_permission=ai_access_permission
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
        grant.status = "revoked"
        grant.revoked_at = datetime.utcnow()
        grant.revoked_reason = revoked_reason
        
        await self.db.flush()
        return True
