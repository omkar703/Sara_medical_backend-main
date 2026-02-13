"""Schemas for Recent Patients List"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

class RecentPatientResponse(BaseModel):
    id: UUID # ID of the link record
    patient_id: UUID
    full_name: str
    mrn: str
    gender: Optional[str] = None
    age: Optional[int] = None # Calculated from DOB
    last_visit_at: datetime
    visit_count: int

    class Config:
        from_attributes = True