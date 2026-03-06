import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base

class DoctorStatus(Base):
    __tablename__ = "doctor_statuses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    status = Column(String, default="inactive", nullable=False) # e.g., "active" or "inactive"
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), default=func.now())