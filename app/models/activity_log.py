
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base

class ActivityLog(Base):
    """Activity log for doctor dashboard"""
    
    __tablename__ = "activity_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Who performed the action
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    
    # What happened
    activity_type = Column(String(100), nullable=False)  # "Lab Results Reviewed", "Operation", "Team Invite Sent"
    description = Column(Text, nullable=True)
    status = Column(String(50), default="completed")  # "completed", "in_review", "pending"
    
    # Related entities
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=True)
    related_entity_type = Column(String(50), nullable=True)  # "appointment", "consultation", "invitation"
    related_entity_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Metadata
    extra_data = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    patient = relationship("Patient", foreign_keys=[patient_id])
    organization = relationship("Organization")
    
    def __repr__(self):
        return f"<ActivityLog {self.activity_type} by User {self.user_id}>"
