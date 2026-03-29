
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field

class AppointmentBase(BaseModel):
    doctor_id: UUID
    requested_date: datetime
    reason: Optional[str] = None

class AppointmentCreate(AppointmentBase):
    grant_access_to_history: Optional[bool] = Field(False, description="Grant doctor access to medical records")

class DoctorAppointmentCreate(BaseModel):
    patient_id: UUID
    requested_date: datetime
    reason: Optional[str] = None

class AppointmentUpdate(BaseModel):
    status: Optional[str] = Field(None, pattern="^(pending|accepted|declined|completed|cancelled|rejected|pending_hospital_approval|approved)$")
    doctor_notes: Optional[str] = None

class AppointmentResponse(AppointmentBase):
    id: UUID
    patient_id: UUID
    status: str
    created_by: str = "patient"
    doctor_notes: Optional[str] = None
    reschedule_note: Optional[str] = None
    doctor_name: Optional[str] = None
    patient_name: Optional[str] = None  # Decrypted patient name from PII encryption
    patient_avatar: Optional[str] = None  # Presigned URL for patient's profile picture
    doctor_avatar: Optional[str] = None  # Presigned URL for doctor's profile picture
    
    # Google Meet / Zoom Implementation
    google_event_id: Optional[str] = None
    meet_link: Optional[str] = None
    meeting_id: Optional[str] = None
    join_url: Optional[str] = None
    start_url: Optional[str] = None
    meeting_password: Optional[str] = None
    
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class AppointmentApproval(BaseModel):
    appointment_time: datetime = Field(..., description="Confirmed time for the appointment")
    doctor_notes: Optional[str] = None

class AppointmentStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(accepted|declined|cancelled|completed|rejected|pending_hospital_approval|approved)$")
    doctor_notes: Optional[str] = None
    reschedule_note: Optional[str] = None
