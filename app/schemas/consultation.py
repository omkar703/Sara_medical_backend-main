"""Consultation Schemas"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ==========================================
# Request Schemas
# ==========================================

class ConsultationCreate(BaseModel):
    """Schema for scheduling a consultation"""
    patientId: UUID
    scheduledAt: datetime
    durationMinutes: int = Field(30, ge=15, le=120)
    notes: Optional[str] = None
    
    @field_validator('scheduledAt')
    @classmethod
    def validate_scheduled_at(cls, v):
        """Ensure scheduled time is in the future"""
        if v.replace(tzinfo=None) < datetime.utcnow():
            raise ValueError('Scheduled time must be in the future')
        return v


class ConsultationUpdate(BaseModel):
    """Schema for updating a consultation"""
    status: Optional[str] = None
    notes: Optional[str] = None
    diagnosis: Optional[str] = None
    prescription: Optional[str] = None
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        """Validate status transitions"""
        allowed = ['scheduled', 'active', 'completed', 'cancelled', 'no_show']
        if v and v not in allowed:
            raise ValueError(f'Status must be one of: {", ".join(allowed)}')
        return v


# ==========================================
# Response Schemas
# ==========================================

class ConsultationResponse(BaseModel):
    """Schema for consultation details"""
    id: str
    scheduledAt: datetime
    durationMinutes: int
    status: str
    
    # Participants
    doctorId: str
    doctorName: Optional[str] = None
    patientId: str
    patientName: Optional[str] = None
    
    # Zoom Info
    meetingId: Optional[str] = None
    joinUrl: Optional[str] = None
    startUrl: Optional[str] = None
    password: Optional[str] = None
    
    # Medical Data
    notes: Optional[str] = None
    diagnosis: Optional[str] = None
    prescription: Optional[str] = None
    
    # AI Data
    aiStatus: str
    hasAudio: bool
    hasTranscript: bool
    hasSoapNote: bool
    
    class Config:
        from_attributes = True


class ConsultationListResponse(BaseModel):
    """Schema for paginated consultation list"""
    consultations: list[ConsultationResponse]
    total: int
    
class DoctorConsultationHistoryRow(BaseModel):
    """
    Row for the Doctor's History Table.
    Shows Patient details instead of Doctor details.
    """
    id: UUID
    scheduled_at: datetime
    status: str  # e.g., 'completed', 'cancelled'
    
    # Flattened Patient Details
    patient_id: UUID
    patient_name: str
    patient_mrn: str
    patient_gender: Optional[str] = None
    
    # Medical Summary
    diagnosis: Optional[str] = None
    
    class Config:
        from_attributes = True
        
class ConsultationSearchRow(BaseModel):
    """
    Schema for Search Results.
    """
    id: UUID
    scheduled_at: datetime
    status: str
    
    # Patient Info (So doctor knows who this is for)
    patient_name: str
    patient_mrn: str
    
    # The Fields we searched
    diagnosis: Optional[str] = None
    prescription: Optional[str] = None
    
    # We won't return the full SOAP note (it's too big), 
    # but the frontend can fetch the details using the ID if needed.
    
    class Config:
        from_attributes = True