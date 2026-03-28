
from typing import List, Optional
from uuid import UUID
from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_current_user, get_organization_id
from app.core.security import pii_encryption

from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services.calendar_service import CalendarService
from app.schemas.calendar import (
    CalendarEventCreate,
    CalendarEventUpdate,
    CalendarEventResponse,
    DayViewResponse,
    MonthViewResponse,
    MonthDaySummary
)


def _map_event_to_response(event) -> CalendarEventResponse:
    """Helper to map ORM event to response model, handling metadata field collision"""
    # 1. Decrypt Staff Member Name (user_name)
    user_name = None
    if hasattr(event, "user") and event.user:
        try:
            user_name = pii_encryption.decrypt(event.user.full_name) if event.user.full_name else "Staff"
        except Exception:
            user_name = event.user.full_name or "Staff"

    event_dict = {
        "id": event.id,
        "user_id": event.user_id,
        "organization_id": event.organization_id,
        "title": event.title,
        "description": event.description,
        "start_time": event.start_time,
        "end_time": event.end_time,
        "all_day": event.all_day,
        "event_type": event.event_type,
        "appointment_id": event.appointment_id,
        "task_id": event.task_id,
        "color": event.color,
        "reminder_minutes": event.reminder_minutes,
        "status": event.status,
        "created_at": event.created_at,
        "updated_at": event.updated_at,
        "user_name": user_name,
        "metadata": {}
    }
    
    # 2. Add metadata for appointment events (Patient & Doctor names)
    if event.event_type == "appointment":
        appt = getattr(event, "appointment", None)
        
        # Safe Decryption helper
        def safe_decrypt(cipher, default):
            if not cipher: return default
            try: return pii_encryption.decrypt(cipher)
            except: return cipher or default

        patient_name = "Patient"
        doctor_name = "Doctor"
        visit_type = "in-person"
        zoom_link = None
        appt_status = event.status

        if appt:
            patient_name = safe_decrypt(getattr(appt.patient, "full_name", None), "Patient")
            doctor_name = safe_decrypt(getattr(appt.doctor, "full_name", None), "Doctor")
            # Correct visit type logic: check for meet link
            visit_type = "video" if (getattr(appt, "meet_link", None) or getattr(appt, "google_event_id", None)) else "in-person"
            zoom_link = getattr(appt, "meet_link", None)
            appt_status = appt.status
        else:
            # Fallback: Recover names from title if relationship is missing (e.g. mock data)
            title = event.title or ""
            if "with Dr. " in title:
                # Patient's view: "Appointment with Dr. Name"
                doctor_name = title.split("with Dr. ")[-1]
                patient_name = user_name if user_name and user_name != "Staff" else "Patient"
            elif "with " in title:
                # Doctor's view: "Appointment with Name"
                patient_name = title.split("with ")[-1]
                doctor_name = user_name if user_name and user_name != "Staff" else "Doctor"

        event_dict["metadata"] = {
            "appointment_status": appt_status,
            "patient_name": patient_name,
            "doctor_name": doctor_name,
            "visit_type": visit_type,
            "zoom_link": zoom_link
        }
    
    return CalendarEventResponse(**event_dict)


router = APIRouter(prefix="/calendar", tags=["Calendar"])


@router.get("/events", response_model=List[CalendarEventResponse])
async def get_calendar_events(
    start_date: datetime = Query(..., description="Start of date range"),
    end_date: datetime = Query(..., description="End of date range"),
    event_type: Optional[str] = Query(None, pattern="^(appointment|custom|task)$", description="Filter by event type"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all calendar events for the current user within a date range.
    Works for all user roles (patient, doctor, admin, hospital).
    """
    calendar_service = CalendarService(db)
    events = await calendar_service.get_events_by_date_range(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        event_type=event_type
    )
    
    # Add metadata for appointment events
    return [_map_event_to_response(event) for event in events]


@router.get("/events/{event_id}", response_model=CalendarEventResponse)
async def get_calendar_event(
    event_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a single calendar event by ID.
    User must own the event.
    """
    calendar_service = CalendarService(db)
    event = await calendar_service.get_event_by_id(event_id, current_user.id)
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendar event not found"
        )
    
    return _map_event_to_response(event)


@router.post("/events", response_model=CalendarEventResponse, status_code=status.HTTP_201_CREATED)
async def create_calendar_event(
    event_data: CalendarEventCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a custom calendar event.
    Available to all user roles.
    """
    calendar_service = CalendarService(db)
    event = await calendar_service.create_custom_event(
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        event_data=event_data
    )
    
    await db.commit()
    await db.refresh(event)
    
    return _map_event_to_response(event)


@router.put("/events/{event_id}", response_model=CalendarEventResponse)
async def update_calendar_event(
    event_id: UUID,
    event_data: CalendarEventUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a calendar event.
    User must own the event.
    Cannot update appointment-linked events (use appointment APIs for that).
    """
    calendar_service = CalendarService(db)
    event = await calendar_service.get_event_by_id(event_id, current_user.id)
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendar event not found"
        )
    
    # Prevent updating appointment-linked events
    if event.event_type == "appointment":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update appointment-linked events. Use appointment APIs instead."
        )
    
    # Prevent updating task-linked events
    if event.event_type == "task":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update task-linked events. Use task APIs instead."
        )
    
    # Update event
    update_dict = event_data.model_dump(exclude_unset=True)
    updated_event = await calendar_service.update_event(event, update_dict)
    
    await db.commit()
    await db.refresh(updated_event)
    
    return _map_event_to_response(updated_event)


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_calendar_event(
    event_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a calendar event.
    User must own the event.
    Cannot delete appointment or task-linked events.
    """
    calendar_service = CalendarService(db)
    event = await calendar_service.get_event_by_id(event_id, current_user.id)
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendar event not found"
        )
    
    # Prevent deleting appointment-linked events
    if event.event_type == "appointment":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete appointment-linked events. Cancel the appointment instead."
        )
    
    # Prevent deleting task-linked events
    if event.event_type == "task":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete task-linked events. Delete the task instead."
        )
    
    await calendar_service.delete_event(event)
    await db.commit()


@router.get("/day/{date}", response_model=DayViewResponse)
async def get_day_view(
    date: date,
    doctor_id: Optional[UUID] = Query(None, description="Filter by doctor ID (Hospital/Admin only)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all events for a specific day.
    Returns appointments, custom events, and tasks for that day.
    """
    calendar_service = CalendarService(db)
    
    # If hospital/admin, fetch for the whole organization
    org_id = None
    if current_user.role in ["hospital", "admin"]:
        org_id = current_user.organization_id
        
    events = await calendar_service.get_day_view(current_user.id, date, organization_id=org_id, doctor_id=doctor_id)
    
    # Transform events to response model
    response_events = [_map_event_to_response(event) for event in events]
    
    return DayViewResponse(
        date=date,
        events=response_events,
        total_count=len(events)
    )


@router.get("/month/{year}/{month}", response_model=MonthViewResponse)
async def get_month_view(
    year: int = Path(..., ge=2000, le=2100, description="Year (e.g., 2024)"),
    month: int = Path(..., ge=1, le=12, description="Month (1-12)"),
    doctor_id: Optional[UUID] = Query(None, description="Filter by doctor ID (Hospital/Admin only)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get summary of all days in a month with event counts.
    Returns day-by-day breakdown with event counts and types.
    """
    calendar_service = CalendarService(db)
    
    # If hospital/admin, fetch for the whole organization
    org_id = None
    if current_user.role in ["hospital", "admin"]:
        org_id = current_user.organization_id

    month_data = await calendar_service.get_month_view(current_user.id, year, month, organization_id=org_id, doctor_id=doctor_id)
    
    # Convert dict to response model
    days_summary = [MonthDaySummary(**day) for day in month_data["days"]]
    
    return MonthViewResponse(
        year=month_data["year"],
        month=month_data["month"],
        days=days_summary,
        total_events=month_data["total_events"]
    )

@router.get("/organization/events", response_model=List[CalendarEventResponse])
async def get_organization_events(
    start_date: datetime = Query(..., description="Start of date range"),
    end_date: datetime = Query(..., description="End of date range"),
    event_type: Optional[str] = Query(None, pattern="^(appointment|custom|task)$", description="Filter by event type"),
    doctor_id: Optional[UUID] = Query(None, description="Filter by doctor ID"),
    visit_type: Optional[str] = Query(None, pattern="^(video|in-person)$", description="Filter by visit mode"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    organization_id: UUID = Depends(get_organization_id)
):
    """
    Get all calendar events for the entire organization.
    Powers the department-wide Shift Schedule UI.
    """
    # Ensure only authorized roles can view the entire department's schedule
    if current_user.role not in ["admin", "hospital", "doctor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Not authorized to view organization schedule"
        )
        
    calendar_service = CalendarService(db)
    events = await calendar_service.get_organization_events(
        organization_id=organization_id,
        start_date=start_date,
        end_date=end_date,
        event_type=event_type,
        doctor_id=doctor_id,
        visit_type=visit_type
    )
    
    return [_map_event_to_response(event) for event in events]