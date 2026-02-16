
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Text, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class CalendarEvent(Base):
    """Calendar Event Model - Unified calendar for all user roles"""
    
    __tablename__ = "calendar_events"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # User and Organization (Multi-tenancy)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Event Details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=False)
    all_day = Column(Boolean, default=False, nullable=False)
    
    # Event Type & Linked Resources
    event_type = Column(
        Enum("appointment", "custom", "task", name="calendar_event_type"),
        nullable=False,
        index=True
    )
    appointment_id = Column(UUID(as_uuid=True), ForeignKey("appointments.id", ondelete="CASCADE"), nullable=True)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=True)
    
    # Customization
    color = Column(String(7), nullable=True)  # Hex color code (e.g., #3B82F6)
    reminder_minutes = Column(Integer, nullable=True)  # Minutes before event to remind
    
    # Status
    status = Column(
        Enum("scheduled", "completed", "cancelled", name="calendar_event_status"),
        default="scheduled",
        nullable=False
    )
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", backref="calendar_events")
    organization = relationship("Organization")
    appointment = relationship("Appointment", backref="calendar_events")
    task = relationship("Task", backref="calendar_events")
    
    def __repr__(self):
        return f"<CalendarEvent {self.title} ({self.event_type})>"
