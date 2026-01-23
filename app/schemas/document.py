"""Pydantic schemas for document management"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ==========================================
# Request Schemas
# ==========================================

class DocumentUploadRequest(BaseModel):
    """Schema for requesting document upload URL"""
    fileName: str = Field(..., min_length=1, max_length=500, description="Original filename")
    fileType: str = Field(..., min_length=1, max_length=50, description="MIME type")
    fileSize: int = Field(..., gt=0, le=104857600, description="File size in bytes (max 100MB)")
    patientId: UUID = Field(..., description="Patient UUID")
    
    @field_validator('fileType')
    @classmethod
    def validate_file_type(cls, v):
        """Validate allowed file types"""
        allowed_types = [
            'application/pdf',
            'image/jpeg',
            'image/png',
            'application/dicom',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ]
        if v not in allowed_types:
            raise ValueError(f'File type must be one of: {", ".join(allowed_types)}')
        return v


class DocumentConfirmRequest(BaseModel):
    """Schema for confirming document upload"""
    metadata: Optional[dict] = Field(None, description="Additional metadata")
    
    @field_validator('metadata')
    @classmethod
    def validate_metadata(cls, v):
        """Validate metadata structure"""
        if v is None:
            return v
        
        # Validate category if present
        if 'category' in v:
            allowed_categories = ['lab-result', 'prescription', 'imaging', 'other']
            if v['category'] not in allowed_categories:
                raise ValueError(f'Category must be one of: {", ".join(allowed_categories)}')
        
        # Validate title length
        if 'title' in v and len(v['title']) > 500:
            raise ValueError('Title must be at most 500 characters')
        
        return v


# ==========================================
# Response Schemas
# ==========================================

class DocumentUploadResponse(BaseModel):
    """Schema for upload URL response"""
    uploadUrl: str = Field(..., description="Presigned upload URL")
    documentId: str = Field(..., description="Document UUID")
    expiresIn: int = Field(..., description="URL expiration time in seconds")


class UploaderInfo(BaseModel):
    """Schema for uploader information"""
    id: str
    name: Optional[str] = None
    
    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    """Schema for document details"""
    id: str
    patientId: str
    fileName: str
    fileType: str
    fileSize: int
    category: Optional[str] = None
    title: Optional[str] = None
    notes: Optional[str] = None
    uploadedAt: str
    uploadedBy: Optional[str] = None
    downloadUrl: Optional[str] = None
    virusScanned: bool
    virusScanResult: Optional[str] = None
    
    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Schema for paginated document list"""
    documents: list[DocumentResponse]
    total: int


# ==========================================
# Success/Error Responses
# ==========================================

class MessageResponse(BaseModel):
    """Generic message response"""
    message: str
