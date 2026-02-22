
from datetime import datetime, date
from typing import Optional, List, Dict
from uuid import UUID
from pydantic import BaseModel, Field, validator


# ================================================
# Base Schemas
# ================================================

class CalendarEventBase(BaseModel):
    """Base schema for calendar events"""
    title: str = Field(..., min_length=1, max_length=255, description="Event title")
    description: Optional[str] = Field(None, description="Event description")
    start_time: datetime = Field(..., description="Event start time")
    end_time: datetime = Field(..., description="Event end time")
    all_day: bool = Field(False, description="Whether event is all-day")
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$", description="Hex color code (e.g., #3B82F6)")
    reminder_minutes: Optional[int] = Field(None, ge=0, le=10080, description="Minutes before event to remind (max 1 week)")
    
    @validator('end_time')
    def end_time_after_start_time(cls, v, values):
        """Validate that end_time is after start_time"""
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('end_time must be after start_time')
        return v


# ================================================
# Request Schemas
# ================================================

class CalendarEventCreate(CalendarEventBase):
    """Schema for creating a custom calendar event"""
    # event_type is always "custom" for user-created events
    # appointment and task events are created automatically
    pass


class CalendarEventUpdate(BaseModel):
    """Schema for updating a calendar event (partial updates allowed)"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    all_day: Optional[bool] = None
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    reminder_minutes: Optional[int] = Field(None, ge=0, le=10080)
    status: Optional[str] = Field(None, pattern="^(scheduled|completed|cancelled)$")
    
    @validator('end_time')
    def end_time_after_start_time(cls, v, values):
        """Validate that end_time is after start_time if both provided"""
        if v and 'start_time' in values and values['start_time']:
            if v <= values['start_time']:
                raise ValueError('end_time must be after start_time')
        return v


# ================================================
# Response Schemas
# ================================================

class CalendarEventResponse(CalendarEventBase):
    """Schema for calendar event response"""
    id: UUID
    user_id: UUID
    organization_id: UUID
    event_type: str  # "appointment", "custom", "task"
    appointment_id: Optional[UUID] = None
    task_id: Optional[UUID] = None
    status: str  # "scheduled", "completed", "cancelled"
    created_at: datetime
    updated_at: datetime
    
    # Optional metadata for appointments
    metadata: Optional[Dict] = Field(None, description="Additional metadata (e.g., patient/doctor names for appointments)")

    class Config:
        from_attributes = True


# ================================================
# View Schemas
# ================================================

class DayViewResponse(BaseModel):
    """Response for day view - all events for a specific day"""
    date: date
    events: List[CalendarEventResponse]
    total_count: int


class MonthDaySummary(BaseModel):
    """Summary for a single day in month view"""
    day: int
    event_count: int
    has_appointments: bool
    has_tasks: bool
    has_custom_events: bool


class MonthViewResponse(BaseModel):
    """Response for month view - summary of all days in a month"""
    year: int
    month: int
    days: List[MonthDaySummary]
    total_events: int

class CalendarEventResponse(CalendarEventBase):
    """Schema for calendar event response"""
    id: UUID
    user_id: UUID
    organization_id: UUID
    event_type: str  # "appointment", "custom", "task"
    appointment_id: Optional[UUID] = None
    task_id: Optional[UUID] = None
    status: str  # "scheduled", "completed", "cancelled"
    created_at: datetime
    updated_at: datetime
    
    # NEW FIELD: To display "Dr. Von" on the org-wide schedule
    user_name: Optional[str] = None
    
    # Optional metadata for appointments
    metadata: Optional[Dict] = Field(None, description="Additional metadata (e.g., patient/doctor names for appointments)")

    class Config:
        from_attributes = True