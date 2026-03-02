"""Audit Log Schemas"""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class AuditLogResponse(BaseModel):
    """Schema for displaying audit log entries"""
    id: UUID
    user_id: Optional[UUID] = None
    organization_id: Optional[UUID] = None
    action: str
    resource_type: str
    resource_id: Optional[UUID] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Optional[Dict] = Field(default=None, alias="metadata_")
    timestamp: datetime

    # Add this validator to automatically cast IPv4Address to string
    @field_validator("ip_address", mode="before")
    @classmethod
    def cast_ip_to_string(cls, v):
        if v is not None:
            return str(v)
        return v

    class Config:
        from_attributes = True
        populate_by_name = True


class AuditLogListResponse(BaseModel):
    """Schema for paginated audit logs"""
    logs: List[AuditLogResponse]
    total: int


class ComplianceReport(BaseModel):
    """Schema for compliance summary statistics"""
    generated_at: datetime
    total_events: int
    phi_access_count: int
    users_active_count: int
    period_start: datetime
    period_end: datetime