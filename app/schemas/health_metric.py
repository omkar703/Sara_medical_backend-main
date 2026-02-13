"""Schemas for Health Metrics"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

class HealthMetricBase(BaseModel):
    metric_type: str
    value: str
    unit: Optional[str] = None
    notes: Optional[str] = None
    recorded_at: datetime

class HealthMetricCreate(HealthMetricBase):
    pass

class HealthMetricResponse(HealthMetricBase):
    id: UUID
    patient_id: UUID

    class Config:
        from_attributes = True