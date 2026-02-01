"""Data Access Grant Model - Tracks patient permission for doctor access to medical records"""

from datetime import datetime
from uuid import UUID
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from app.database import Base


class DataAccessGrant(Base):
    """
    Tracks explicit patient permission for doctors to access medical records.
    HIPAA compliance: No doctor access without documented patient consent.
    """
    __tablename__ = "data_access_grants"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Permission relationship
    patient_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    doctor_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Optional link to appointment
    appointment_id = Column(PG_UUID(as_uuid=True), ForeignKey("appointments.id"), nullable=True)
    
    # Grant metadata
    grant_reason = Column(String(255), nullable=True)
    ai_access_permission = Column(Boolean, default=False, nullable=False)
    access_level = Column(String(50), default="read_only", nullable=False) # 'read_only', 'read_analyze'
    granted_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Status tracking (pending, active, revoked, expired)
    status = Column(String(20), default="active", nullable=False)
    
    # Revocation tracking
    is_active = Column(Boolean, default=True, nullable=False) # Deprecated in favor of status, kept for safety
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revoked_reason = Column(Text, nullable=True)
    
    # Audit
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    patient = relationship("User", foreign_keys=[patient_id], backref="access_grants_given")
    doctor = relationship("User", foreign_keys=[doctor_id], backref="access_grants_received")
    appointment = relationship("Appointment", backref="data_access_grants")
    
    def __repr__(self):
        return f"<DataAccessGrant {self.id} P:{self.patient_id} D:{self.doctor_id}>"
