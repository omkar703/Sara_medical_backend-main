
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field

class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: str = Field(default="normal", pattern="^(urgent|normal)$")
    status: str = Field(default="pending", pattern="^(pending|completed)$")

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: Optional[str] = Field(None, pattern="^(urgent|normal)$")
    status: Optional[str] = Field(None, pattern="^(pending|completed)$")

class TaskResponse(TaskBase):
    id: UUID
    doctor_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
