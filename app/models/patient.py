"""Patient Model"""

from datetime import datetime, date
from typing import List, Optional
from uuid import UUID

from sqlalchemy import Date, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Patient(Base):
    """
    Patient model with encrypted PII and soft delete support
    """
    __tablename__ = "patients"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    mrn: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    
    # Encrypted fields (stored as massive strings)
    full_name: Mapped[str] = mapped_column(String(500), nullable=False)
    date_of_birth: Mapped[str] = mapped_column(String(500), nullable=False)  # Encrypted date string
    gender: Mapped[str] = mapped_column(String(20), nullable=True)
    phone_number: Mapped[str] = mapped_column(String(500), nullable=True)
    email: Mapped[str] = mapped_column(String(500), nullable=True)
    
    # JSON Encrypted fields
    address: Mapped[dict] = mapped_column(JSONB, nullable=True)
    emergency_contact: Mapped[dict] = mapped_column(JSONB, nullable=True)
    
    # Medical info (Encrypted)
    medical_history: Mapped[str] = mapped_column(String, nullable=True)
    allergies: Mapped[List[str]] = mapped_column(JSONB, nullable=True)
    medications: Mapped[List[str]] = mapped_column(JSONB, nullable=True)
    
    # Metadata
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime] = mapped_column(nullable=True)

    # Relationships
    organization = relationship("Organization", backref="patients")
    creator = relationship("User", foreign_keys=[created_by])
    documents = relationship("Document", back_populates="patient", cascade="all, delete-orphan")

    __mapper_args__ = {"eager_defaults": True}
