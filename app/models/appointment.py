
import uuid
from datetime import datetime
from uuid import UUID
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.database import Base

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    doctor_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    patient_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    requested_date = Column(DateTime(timezone=True), nullable=False)
    reason = Column(Text, nullable=True)
    
    status = Column(Enum("pending", "accepted", "declined", "completed", "cancelled", name="appointment_status"), default="pending", nullable=False)
    
    # Zoom Integration Fields
    meeting_id = Column(String(50), nullable=True)
    join_url = Column(Text, nullable=True)
    start_url = Column(Text, nullable=True)
    meeting_password = Column(String(50), nullable=True)
    
    doctor_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    doctor = relationship("User", foreign_keys=[doctor_id], backref="doctor_appointments")
    patient = relationship("User", foreign_keys=[patient_id], backref="patient_appointments")
    
    def __repr__(self):
        return f"<Appointment {self.id} {self.status}>"
