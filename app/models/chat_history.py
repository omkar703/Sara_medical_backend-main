"""Chat History Model"""

from datetime import datetime
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class ChatHistory(Base):
    """
    Stores AI chat conversations.
    """
    __tablename__ = "chat_history"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    conversation_id = Column(String(100), nullable=False, index=True)
    patient_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    doctor_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True) # Null if patient chat
    document_id = Column(PG_UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True)
    
    user_type = Column(String(20), nullable=False) # 'patient' or 'doctor'
    role = Column(String(20), nullable=False) # 'user', 'assistant', 'doctor'
    
    content = Column(Text, nullable=False)
    sources = Column(JSONB, nullable=True) # List of chunk IDs or citations
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    # Relationships
    patient = relationship("User", foreign_keys=[patient_id])
    doctor = relationship("User", foreign_keys=[doctor_id])
    document = relationship("Document")

    def __repr__(self):
        return f"<ChatHistory {self.id} Conv:{self.conversation_id}>"
