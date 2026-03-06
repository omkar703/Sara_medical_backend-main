
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy import JSON
from app.database import Base

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Notification Details
    type = Column(String(50), nullable=False)  # appointment_requested, access_granted, etc.
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    action_url = Column(String(255), nullable=True)

    # Optional reference to a DataAccessGrant (for access-request notifications)
    # Allows the patient to approve/reject the grant directly from the notification
    grant_id = Column(UUID(as_uuid=True), ForeignKey("data_access_grants.id", ondelete="SET NULL"), nullable=True, index=True)
    # Metadata payload for action buttons (e.g., doctor info to display)
    action_metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", backref="notifications")
    organization = relationship("Organization")

    def __repr__(self):
        return f"<Notification {self.title} (Read: {self.is_read})>"
