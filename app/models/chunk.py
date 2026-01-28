"""Chunk Model - Stores semantic chunks of processed documents"""

import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import Column, ForeignKey, String, Text, Integer, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from app.database import Base


class Chunk(Base):
    """
    Stores processed chunks of documents for AI retrieval.
    """
    __tablename__ = "chunks"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Relationships
    document_id = Column(PG_UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Chunk Content
    content = Column(Text, nullable=False)
    source = Column(String(50), nullable=False)  # 'TIER_1_TEXT', 'TIER_3_IMAGE_ANALYSIS'
    chunk_type = Column(String(50), nullable=False) # 'text', 'table', 'form', 'image_analysis'
    page_number = Column(Integer, nullable=True)
    
    # AI Metadata
    medical_keywords = Column(JSONB, nullable=True) # List of keywords
    embedding = Column(Vector(1536), nullable=True) # Titan dimension is 1536
    
    # Audit
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    # Relationships
    document = relationship("Document", backref="chunks")
    patient = relationship("User", foreign_keys=[patient_id])

    def __repr__(self):
        return f"<Chunk {self.id} Doc:{self.document_id} Type:{self.chunk_type}>"
