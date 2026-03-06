from pydantic import BaseModel, Field, EmailStr
from typing import List , Optional 
from app.schemas.doctor import DoctorSearchItem
from datetime import datetime
from uuid import UUID

# Request schema for the doctor setting their status
class DoctorStatusUpdateRequest(BaseModel):
    status: str = Field(..., description="Must be 'active' or 'inactive'")

# Response schema for the doctor's update action
class DoctorStatusResponse(BaseModel):
    message: str
    status: str

# Extended search item that includes the current status
class DoctorWithStatusItem(DoctorSearchItem):
    status: str

# Response schema for the hospital dashboard
class HospitalDoctorStatusListResponse(BaseModel):
    active_doctors: List[DoctorWithStatusItem]
    inactive_doctors: List[DoctorWithStatusItem]
    
class DoctorDetailedWithStatusItem(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    specialty: Optional[str] = None
    photo_url: Optional[str] = None
    department: Optional[str] = None
    department_role: Optional[str] = None
    phone_number: Optional[str] = None
    license_number: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None
    status: str

    class Config:
        from_attributes = True

class HospitalDoctorStatusListResponse(BaseModel):
    active_doctors: List[DoctorDetailedWithStatusItem]
    inactive_doctors: List[DoctorDetailedWithStatusItem]