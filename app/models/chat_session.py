"""Chat Session and Chat Message Models - Persistent AI Chat History"""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class ChatSession(Base):
    """
    Represents a named, persistent AI chat session between a doctor and a patient.
    One session = one "conversation thread" similar to a ChatGPT conversation.
    """
    __tablename__ = "chat_sessions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Ownership
    doctor_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id = Column(PG_UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)

    # Metadata
    title = Column(String(255), nullable=True, default=None)  # Null until first message auto-generates it

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    doctor = relationship("User", foreign_keys=[doctor_id])
    patient = relationship("Patient", foreign_keys=[patient_id])
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.created_at")

    def __repr__(self):
        return f"<ChatSession {self.id} Doctor:{self.doctor_id} Patient:{self.patient_id} Title:{self.title}>"


class ChatMessage(Base):
    """
    Stores a single message in a ChatSession.
    Role is either 'doctor' (user's input) or 'assistant' (AI's response).
    """
    __tablename__ = "chat_messages"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Parent session
    session_id = Column(PG_UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)

    # Message content
    role = Column(String(20), nullable=False)      # 'doctor' or 'assistant'
    content = Column(Text, nullable=False)

    # AI metadata (only populated on assistant messages)
    sources = Column(JSONB, nullable=True)          # List of chunk source labels cited
    confidence = Column(String(20), nullable=True)  # 'high', 'medium', 'low'

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    session = relationship("ChatSession", back_populates="messages")

    def __repr__(self):
        return f"<ChatMessage {self.id} Session:{self.session_id} Role:{self.role}>"
