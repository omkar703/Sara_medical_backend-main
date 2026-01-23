"""Document Model"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, BigInteger, DateTime, ForeignKey, String, Text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Document(Base):
    """Document model for storing file metadata"""
    
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Relationships
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # File metadata
    file_name = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    storage_path = Column(String(1000), nullable=False, unique=True)
    
    # Categorization
    category = Column(
        String(100), 
        nullable=True
    )  # 'LAB_REPORT', 'PAST_PRESCRIPTION', 'IMAGING', 'OTHER'
    title = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Tracking
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    uploaded_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    # Security
    virus_scanned = Column(Boolean, default=False, nullable=False)
    virus_scan_result = Column(String(50), nullable=True)  # 'clean', 'infected', 'error'
    
    # Soft delete
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('file_size > 0 AND file_size <= 104857600', name='chk_file_size'),
    )
    
    # Relationships
    patient = relationship("Patient", back_populates="documents")
    uploader = relationship("User", foreign_keys=[uploaded_by])
    
    def __repr__(self):
        return f"<Document {self.file_name}>"
