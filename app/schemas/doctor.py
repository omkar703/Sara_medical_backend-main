from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

class DoctorProfileUpdate(BaseModel):
    specialty: Optional[str] = Field(None, description="Doctor specialty (e.g., Cardiology, Dermatology)")
    license_number: Optional[str] = Field(None, description="Medical license number")

class DoctorSearchItem(BaseModel):
    id: UUID
    full_name: str = Field(..., alias="name")
    specialty: Optional[str]
    avatar_url: Optional[str] = Field(None, alias="photo_url")

    class Config:
        populate_by_name = True
        from_attributes = True

class DoctorSearchResponse(BaseModel):
    results: List[DoctorSearchItem]
