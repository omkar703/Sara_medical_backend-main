"""Consultation Model"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Consultation(Base):
    """
    Consultation model for video appointments
    """
    __tablename__ = "consultations"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    
    # Timing
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    duration_minutes: Mapped[int] = mapped_column(default=30)
    
    # Participants
    doctor_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    patient_id: Mapped[UUID] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Status: scheduled, active, completed, cancelled, no_show
    status: Mapped[str] = mapped_column(String(20), default="scheduled", index=True)
    
    # Zoom Integration
    meeting_id: Mapped[str] = mapped_column(String(50), nullable=True)
    join_url: Mapped[str] = mapped_column(Text, nullable=True)
    start_url: Mapped[str] = mapped_column(Text, nullable=True)
    password: Mapped[str] = mapped_column(String(50), nullable=True)
    
    # Medical Data
    notes: Mapped[str] = mapped_column(Text, nullable=True)  # Doctor's manual notes
    diagnosis: Mapped[str] = mapped_column(Text, nullable=True)
    prescription: Mapped[str] = mapped_column(Text, nullable=True)
    
    # AI Analysis Data
    audio_recording_path: Mapped[str] = mapped_column(String(500), nullable=True)
    transcript: Mapped[str] = mapped_column(Text, nullable=True)
    soap_note: Mapped[dict] = mapped_column(JSONB, nullable=True)  # Structured SOAP note from AI
    ai_status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, processing, completed, failed
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[datetime] = mapped_column(nullable=True)

    # Relationships
    doctor = relationship("User", foreign_keys=[doctor_id], backref="consultations")
    patient = relationship("Patient", backref="consultations")
    organization = relationship("Organization")
