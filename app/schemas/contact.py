"""Contact Message Schemas"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class ContactMessageCreate(BaseModel):
    """Schema for creating a contact message"""
    first_name: str = Field(..., min_length=1, max_length=255, description="First name of the sender", alias="firstName")
    last_name: str = Field(..., min_length=1, max_length=255, description="Last name of the sender", alias="lastName")
    email: EmailStr = Field(..., description="Email address of the sender")
    phone: str = Field(..., min_length=7, max_length=20, description="Phone number of the sender")
    subject: str = Field(..., min_length=1, max_length=255, description="Subject of the message")
    message: str = Field(..., min_length=1, max_length=5000, description="Message content")
    
    class Config:
        populate_by_name = True  # Allow both snake_case and camelCase


class ContactMessageResponse(BaseModel):
    """Schema for contact message response"""
    id: UUID
    first_name: str
    last_name: str
    email: str
    phone: str
    subject: str
    message: str
    read: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ContactMessageListResponse(BaseModel):
    """Schema for listing contact messages"""
    id: UUID
    first_name: str
    last_name: str
    email: str
    subject: str
    read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ContactMessageSuccessResponse(BaseModel):
    """Schema for successful contact message submission"""
    success: bool = True
    message: str = "Your message has been received. We will get back to you shortly."
    id: UUID
