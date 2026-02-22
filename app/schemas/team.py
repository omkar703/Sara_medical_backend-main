from pydantic import BaseModel, EmailStr, Field
from enum import Enum
from datetime import datetime
from typing import Optional
from uuid import UUID

class TeamRoleEnum(str, Enum):
    ADMINISTRATOR = "ADMINISTRATOR"
    MEMBER = "MEMBER"
    PATIENT = "PATIENT"

class TeamRole(BaseModel):
    role: TeamRoleEnum = Field(..., description="Role identifier")
    description: str = Field(..., description="Human readable description of the role")

    class Config:
        use_enum_values = True

class TeamInviteCreate(BaseModel):
    full_name: str = Field(..., description="Full name of the invitee")
    email: EmailStr = Field(..., description="Email address of the invitee")
    department_id: str = Field(..., description="UUID of the department/organization")
    department_role: str = Field(..., description="Specific title, e.g., Senior Physician")
    role: TeamRoleEnum = Field(..., description="Base system role")

    class Config:
        use_enum_values = True
        
class StaffMemberResponse(BaseModel):
    """Schema for the Department Staff Roster table"""
    id: UUID
    name: str
    email: str
    role: str # E.g., 'Chief Cardiologist', 'Senior Physician'
    last_accessed: Optional[datetime] = None
    status: str # 'Active', 'On Leave', 'Inactive'

    class Config:
        from_attributes = True

class PendingInviteResponse(BaseModel):
    """Schema for the Pending Invites side-panel"""
    id: UUID
    email: str
    role: str
    expires_at: datetime
    status: str

    class Config:
        from_attributes = True
