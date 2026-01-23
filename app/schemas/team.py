from pydantic import BaseModel, EmailStr, Field
from enum import Enum

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
    role: TeamRoleEnum = Field(..., description="Role to assign to the invitee")

    class Config:
        use_enum_values = True
