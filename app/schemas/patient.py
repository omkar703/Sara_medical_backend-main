"""Pydantic Schemas for Patient Management"""

from datetime import date, datetime
from typing import List, Optional
from uuid import UUID
import phonenumbers

from pydantic import BaseModel, EmailStr, Field, validator


# ==========================================
# Nested Schemas
# ==========================================

class AddressSchema(BaseModel):
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = Field(None, alias="zipCode")
    
    class Config:
        populate_by_name = True


class EmergencyContactSchema(BaseModel):
    name: Optional[str] = None
    relationship: Optional[str] = None
    phone_number: Optional[str] = Field(None, alias="phoneNumber")
    
    class Config:
        populate_by_name = True
        
    @validator('phone_number')
    def validate_ec_phone(cls, v):
        if not v: return v
        try:
            n = phonenumbers.parse(v, None)
            if not phonenumbers.is_valid_number(n):
                raise ValueError('Invalid phone number')
            return phonenumbers.format_number(n, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException:
            raise ValueError('Invalid phone number format. Use E.164 (e.g. +1234567890)')


# ==========================================
# Patient Schemas
# ==========================================

class PatientBase(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=100, alias="fullName")
    date_of_birth: date = Field(..., alias="dateOfBirth")
    gender: Optional[str] = Field(None, pattern="^(male|female|other|prefer_not_to_say)$")
    phone_number: Optional[str] = Field(None, alias="phoneNumber")
    email: Optional[EmailStr] = None
    address: Optional[AddressSchema] = None
    emergency_contact: Optional[EmergencyContactSchema] = Field(None, alias="emergencyContact")
    medical_history: Optional[str] = Field(None, alias="medicalHistory")
    allergies: Optional[List[str]] = []
    medications: Optional[List[str]] = []

    class Config:
        populate_by_name = True

    @validator("date_of_birth")
    def date_of_birth_not_future(cls, v):
        if v > date.today():
            raise ValueError("Date of birth cannot be in the future")
        return v

    @validator('phone_number')
    def validate_phone(cls, v):
        if not v: return v
        try:
            n = phonenumbers.parse(v, None)
            if not phonenumbers.is_valid_number(n):
                raise ValueError('Invalid phone number')
            return phonenumbers.format_number(n, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException:
            raise ValueError('Invalid phone number format. Use E.164 (e.g. +1234567890)')


class PatientCreate(PatientBase):
    pass


class PatientOnboard(PatientBase):
    password: str = Field(..., min_length=8, max_length=100)


class PatientUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=100, alias="fullName")
    date_of_birth: Optional[date] = Field(None, alias="dateOfBirth")
    gender: Optional[str] = Field(None, pattern="^(male|female|other|prefer_not_to_say)$")
    phone_number: Optional[str] = Field(None, alias="phoneNumber")
    email: Optional[EmailStr] = None
    address: Optional[AddressSchema] = None
    emergency_contact: Optional[EmergencyContactSchema] = Field(None, alias="emergencyContact")
    medical_history: Optional[str] = Field(None, alias="medicalHistory")
    allergies: Optional[List[str]] = None
    medications: Optional[List[str]] = None

    class Config:
        populate_by_name = True

    @validator("date_of_birth")
    def date_of_birth_not_future(cls, v):
        if v and v > date.today():
            raise ValueError("Date of birth cannot be in the future")
        return v


class PatientResponse(PatientBase):
    id: UUID
    mrn: str
    organization_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        populate_by_name = True
        from_attributes = True


class PatientListItem(BaseModel):
    id: UUID
    mrn: str
    full_name: str = Field(..., alias="fullName")
    date_of_birth: date = Field(..., alias="dateOfBirth")
    gender: Optional[str] = None
    phone_number: Optional[str] = Field(None, alias="phoneNumber")
    email: Optional[str]
    created_at: datetime
    
    class Config:
        populate_by_name = True


class PatientListResponse(BaseModel):
    items: List[PatientListItem] = Field(..., alias="patients")
    total: int
    page: int
    pages: int
    
    class Config:
        populate_by_name = True
