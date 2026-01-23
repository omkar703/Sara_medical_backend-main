"""Medical History Schemas"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentCategory(str, Enum):
    """Medical document categories"""
    LAB_REPORT = "LAB_REPORT"
    PAST_PRESCRIPTION = "PAST_PRESCRIPTION"
    IMAGING = "IMAGING"
    OTHER = "OTHER"


class MedicalHistoryUpload(BaseModel):
    """Schema for medical history file upload request"""
    category: DocumentCategory
    description: Optional[str] = Field(None, max_length=500)
    title: Optional[str] = Field(None, max_length=200)


class MedicalHistoryResponse(BaseModel):
    """Schema for medical history document response with presigned URL"""
    id: UUID
    file_name: str
    category: str
    title: Optional[str]
    description: Optional[str] = Field(None, alias="notes")
    file_size: int
    uploaded_at: datetime
    presigned_url: str = Field(..., description="Temporary URL (15 min expiration)")
    
    class Config:
        from_attributes = True
        populate_by_name = True


class DocumentAccessRequest(BaseModel):
    """Schema for requesting access to patient documents"""
    patient_id: UUID
