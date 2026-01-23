"""AI Processing Queue Model - Infrastructure for future AI integration"""

from datetime import datetime
from uuid import UUID
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, Enum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class AIProcessingQueue(Base):
    """
    Queue system for AI processing requests.
    Maintains strict patient-data tagging for privacy compliance.
    """
    __tablename__ = "ai_processing_queue"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Participants
    patient_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    doctor_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    organization_id = Column(PG_UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Processing data
    data_payload = Column(JSONB, nullable=False)  # Contains file IDs or text notes
    request_type = Column(String(50), nullable=False)  # e.g., 'diagnosis_assist', 'summary_generation'
    
    # Status tracking
    status = Column(
        Enum("pending", "processing", "completed", "failed", name="ai_queue_status"),
        default="pending",
        nullable=False,
        index=True
    )
    
    # Results
    result_data = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Processing timestamps
    queued_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    processing_started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Audit
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    patient = relationship("User", foreign_keys=[patient_id], backref="ai_requests_as_patient")
    doctor = relationship("User", foreign_keys=[doctor_id], backref="ai_requests_as_doctor")
    organization = relationship("Organization", backref="ai_processing_queue")
    
    def __repr__(self):
        return f"<AIProcessingQueue {self.id} {self.status}>"
