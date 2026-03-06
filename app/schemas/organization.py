"""Organization and Invitation Schemas"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from typing import List
from pydantic import BaseModel, EmailStr, Field, field_validator


# ==========================================
# Organization Schemas
# ==========================================

class OrganizationUpdate(BaseModel):
    """Schema for updating organization profile"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)

class OrganizationResponse(BaseModel):
    id: UUID
    name: str
    subscription_tier: str
    departments: Optional[str] = None # Added field
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==========================================
# Member Management Schemas
# ==========================================

class MemberResponse(BaseModel):
    id: UUID
    full_name: str
    email: EmailStr
    role: str
    specialty: Optional[str] = None
    department: Optional[str] = None       # Added field
    department_role: Optional[str] = None  # Added field
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class MemberRoleUpdate(BaseModel):
    """Schema for updating a member's role"""
    role: str
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        allowed = ['admin', 'doctor', 'nurse', 'staff']
        if v not in allowed:
            # We map app roles to user_role enum (which only has patient, doctor, admin)
            # For this MVP, we might only strictly support 'doctor' and 'admin'
            # as per user_role enum in database
            pass
        return v


# ==========================================
# Invitation Schemas
# ==========================================

class InvitationCreate(BaseModel):
    email: EmailStr
    role: str = "doctor"
    department: Optional[str] = None       # Added field
    department_role: Optional[str] = None
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        allowed = ['doctor', 'admin']  # Restricted for now
        if v not in allowed:
            raise ValueError(f"Role must be one of: {', '.join(allowed)}")
        return v


class InvitationResponse(BaseModel):
    """Schema for invitation details"""
    id: UUID
    email: EmailStr
    role: str
    status: str
    expires_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


class InvitationAccept(BaseModel):
    token: str
    full_name: str
    password: str = Field(..., min_length=8)
    specialty: Optional[str] = None
    license_number: Optional[str] = None
    department: Optional[str] = None       # Added field
    department_role: Optional[str] = None  # Added field

class DepartmentListResponse(BaseModel):
    """Schema for returning the list of departments"""
    departments: List[str]