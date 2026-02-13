"""Recent Patient Model (Doctor's History)"""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base

class RecentPatient(Base):
    __tablename__ = "recent_patients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Links
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Metadata
    last_visit_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    visit_count = Column(Integer, default=1, nullable=False)
    
    # Relationships
    doctor = relationship("User", foreign_keys=[doctor_id])
    patient = relationship("Patient", foreign_keys=[patient_id])

    def __repr__(self):
        return f"<RecentPatient Doc={self.doctor_id} Pat={self.patient_id}>"