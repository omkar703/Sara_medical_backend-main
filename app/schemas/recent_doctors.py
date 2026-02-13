"""Schemas for Recent Doctors List"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

class RecentDoctorResponse(BaseModel):
    id: UUID # ID of the link record
    doctor_id: UUID
    doctor_name: str
    specialty: Optional[str] = "General Physician"
    avatar_url: Optional[str] = None
    last_visit_at: datetime
    visit_count: int

    class Config:
        from_attributes = True