"""Pydantic schemas for authentication"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, validator


# ==========================================
# User Schemas
# ==========================================

class UserCreate(BaseModel):
    """Schema for user registration"""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    confirm_password: Optional[str] = None
    first_name: Optional[str] = "Unknown"
    last_name: Optional[str] = "User"
    phone: Optional[str] = None
    phone_number: Optional[str] = None
    role: str = Field(..., pattern="^(patient|doctor|admin|hospital)$")
    organization_name: Optional[str] = "Default Org"
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if v and 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v
    
    @validator('password')
    def password_strength(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        # Relaxed constraints for demo purposes if needed, otherwise keep strict
        return v


class UserResponse(BaseModel):
    """Schema for user response"""
    id: UUID
    name: str # Added combined name
    email: EmailStr
    first_name: str
    last_name: str
    phone_number: Optional[str]
    role: str
    organization_id: UUID
    mfa_enabled: bool
    email_verified: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ==========================================
# Authentication Schemas
# ==========================================

class LoginRequest(BaseModel):
    """Schema for login request"""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Schema for successful login (without MFA)"""
    success: bool = True
    token: str
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class MFARequiredResponse(BaseModel):
    """Schema when MFA is required"""
    mfa_required: bool = True
    user_id: str
    message: str = "MFA verification required"


class VerifyMFARequest(BaseModel):
    """Schema for MFA verification"""
    user_id: str
    code: str = Field(..., min_length=6, max_length=8)


class SetupMFAResponse(BaseModel):
    """Schema for MFA setup response"""
    secret: str
    qr_code: str  # Base64 encoded QR code image
    backup_codes: list[str]


class VerifyMFASetupRequest(BaseModel):
    """Schema for verifying MFA setup"""
    code: str = Field(..., min_length=6, max_length=6)


# ==========================================
# Email Verification Schemas
# ==========================================

class VerifyEmailRequest(BaseModel):
    """Schema for email verification"""
    token: str


# ==========================================
# Password Reset Schemas
# ==========================================

class ForgotPasswordRequest(BaseModel):
    """Schema for forgot password request"""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Schema for password reset"""
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str = Field(..., min_length=8, max_length=100)
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


# ==========================================
# Token Schemas
# ==========================================

class RefreshTokenRequest(BaseModel):
    """Schema for token refresh request"""
    refresh_token: str


class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str
    token_type: str = "bearer"


# ==========================================
# Success/Error Responses
# ==========================================

class MessageResponse(BaseModel):
    """Generic message response"""
    message: str


class ErrorResponse(BaseModel):
    """Error response schema"""
    error: str
    detail: Optional[str] = None
