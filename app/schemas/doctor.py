from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

class DoctorProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(None, description="Doctor's full display name")
    specialty: Optional[str] = Field(None, description="Doctor specialty")
    license_number: Optional[str] = Field(None, description="Medical license number")
    department: Optional[str] = Field(None, description="Assigned department")
    department_role: Optional[str] = Field(None, description="Role within the department")

class DoctorSearchItem(BaseModel):
    id: UUID
    full_name: str = Field(..., alias="name")
    specialty: Optional[str]
    avatar_url: Optional[str] = Field(None, alias="photo_url")
    department: Optional[str] = None
    department_role: Optional[str] = None

    class Config:
        populate_by_name = True
        from_attributes = True

class DoctorSearchResponse(BaseModel):
    results: List[DoctorSearchItem]
