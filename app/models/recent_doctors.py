"""Recent Doctor Model (My Care Team)"""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base

class RecentDoctor(Base):
    __tablename__ = "recent_doctors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Links
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Metadata
    last_visit_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    visit_count = Column(Integer, default=1, nullable=False)
    
    # Relationships (Eager load the doctor details)
    doctor = relationship("User", foreign_keys=[doctor_id])
    patient = relationship("Patient", foreign_keys=[patient_id])

    def __repr__(self):
        return f"<RecentDoctor Pat={self.patient_id} Doc={self.doctor_id}>"