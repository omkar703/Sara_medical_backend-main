
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

class AppointmentUpdate(BaseModel):
    status: Optional[str] = Field(None, pattern="^(pending|accepted|declined|completed|cancelled)$")
    doctor_notes: Optional[str] = None

class AppointmentResponse(AppointmentBase):
    id: UUID
    patient_id: UUID
    status: str
    doctor_notes: Optional[str] = None
    
    # Google Meet Implementation
    google_event_id: Optional[str] = None
    meet_link: Optional[str] = None
    
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class AppointmentApproval(BaseModel):
    appointment_time: datetime = Field(..., description="Confirmed time for the appointment")
    doctor_notes: Optional[str] = None

class AppointmentStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(accepted|declined)$")
    doctor_notes: Optional[str] = None
