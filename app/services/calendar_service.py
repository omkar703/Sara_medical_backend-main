from typing import List, Optional
from uuid import UUID
from datetime import datetime, date, timedelta, timezone as dt_timezone
import pytz
from sqlalchemy import select, and_, extract, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calendar_event import CalendarEvent
from app.models.appointment import Appointment
from app.models.task import Task
from app.schemas.calendar import CalendarEventCreate
from app.services.notification_service import NotificationService
from app.core.security import pii_encryption


class CalendarService:
    """Service layer for calendar operations and synchronization"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_events_by_date_range(
        self,
        user_id: UUID,
        start_date: datetime,
        end_date: datetime,
        event_type: Optional[str] = None
    ) -> List[CalendarEvent]:
        """
        Get all calendar events for a user within a date range
        
        Args:
            user_id: User UUID
            start_date: Start of date range
            end_date: End of date range
            event_type: Optional filter by event type ("appointment", "custom", "task")
        
        Returns:
            List of CalendarEvent objects
        """
        from sqlalchemy.orm import selectinload
        query = select(CalendarEvent).where(
            and_(
                CalendarEvent.user_id == user_id,
                CalendarEvent.start_time >= start_date,
                CalendarEvent.start_time <= end_date
            )
        ).options(
            selectinload(CalendarEvent.appointment).selectinload(Appointment.doctor),
            selectinload(CalendarEvent.appointment).selectinload(Appointment.patient),
            selectinload(CalendarEvent.task)
        )
        
        if event_type:
            query = query.where(CalendarEvent.event_type == event_type)
        
        query = query.order_by(CalendarEvent.start_time.asc())
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_event_by_id(self, event_id: UUID, user_id: UUID) -> Optional[CalendarEvent]:
        """
        Get a single calendar event by ID
        
        Args:
            event_id: Event UUID
            user_id: User UUID (for authorization)
        
        Returns:
            CalendarEvent or None
        """
        from sqlalchemy.orm import selectinload
        query = select(CalendarEvent).where(
            and_(
                CalendarEvent.id == event_id,
                CalendarEvent.user_id == user_id
            )
        ).options(
            selectinload(CalendarEvent.appointment).selectinload(Appointment.doctor),
            selectinload(CalendarEvent.appointment).selectinload(Appointment.patient),
            selectinload(CalendarEvent.task)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def create_custom_event(
        self,
        user_id: UUID,
        organization_id: UUID,
        event_data: CalendarEventCreate
    ) -> CalendarEvent:
        """
        Create a custom calendar event
        
        Args:
            user_id: User UUID
            organization_id: Organization UUID
            event_data: Event data from request
        
        Returns:
            Created CalendarEvent
        """
        event = CalendarEvent(
            user_id=user_id,
            organization_id=organization_id,
            event_type="custom",
            title=event_data.title,
            description=event_data.description,
            start_time=event_data.start_time,
            end_time=event_data.end_time,
            all_day=event_data.all_day,
            color=event_data.color,
            reminder_minutes=event_data.reminder_minutes,
            status="scheduled"
        )
        
        self.db.add(event)
        await self.db.flush()
        await self.db.refresh(event)
        
        # Notify User of custom event
        notification_service = NotificationService(self.db)
        await notification_service.create_notification(
            user_id=user_id,
            organization_id=organization_id,
            type="calendar_event",
            title="Calendar Event Created",
            message=f"Event '{event.title}' has been added to your calendar.",
            action_url=f"/calendar?date={event.start_time.strftime('%Y-%m-%d')}"
        )
        
        return event
    
    async def update_event(
        self,
        event: CalendarEvent,
        update_data: dict
    ) -> CalendarEvent:
        """
        Update a calendar event
        
        Args:
            event: CalendarEvent to update
            update_data: Dictionary of fields to update
        
        Returns:
            Updated CalendarEvent
        """
        for field, value in update_data.items():
            if value is not None:
                setattr(event, field, value)
        
        event.updated_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(event)
        
        return event
    
    async def delete_event(self, event: CalendarEvent) -> None:
        """
        Delete a calendar event
        
        Args:
            event: CalendarEvent to delete
        """
        await self.db.delete(event)
        await self.db.flush()

    async def _get_org_tz_by_id(self, organization_id: UUID):
        """Helper to get organization timezone by ID"""
        from app.models.user import Organization
        query = select(Organization.timezone).where(Organization.id == organization_id)
        result = await self.db.execute(query)
        org_tz_str = result.scalar_one_or_none()
        try:
            return pytz.timezone(org_tz_str or "UTC")
        except Exception:
            return pytz.UTC
    
    async def sync_appointment_to_calendar(
        self,
        appointment: Appointment,
        action: str  # "create", "update", "cancel"
    ) -> None:
        """
        Sync an appointment to calendar events for both patient and doctor
        
        Args:
            appointment: Appointment object
            action: Action to perform ("create", "update", "cancel")
        """
        # If doctor created it, it starts as 'pending'. 
        # We don't want to show it on calendar as "Scheduled" until it's accepted.
        # So for 'create' action, we only proceed if status is 'accepted' 
        # (which happens for patient-initiated ones immediately if approved, 
        # though usually patient-initiated ones are 'pending' too... 
        # wait, let me check the normal flow).
        
        if action == "create":
            # For doctor-created: starts pending. Don't create events yet.
            # For patient-created: starts pending. Usually we only create events when ACCEPTED.
            # Let's enforce: Only create events if status is 'accepted' or if it's a standard flow that requires it.
            if appointment.status == "accepted":
                await self._create_appointment_events(appointment)
            elif appointment.created_by == "doctor":
                # Don't create events for pending doctor requests
                return
            else:
                # Normal patient request creation - maybe we want it on calendar as pending?
                # User said "Appointment not showing in calendar" for doctor created ones.
                # If they want it to show while pending, we stay with previous logic.
                # But they said "accept/decline is redundant for doctor".
                # Let's show it if it's accepted.
                if appointment.status == "accepted":
                    await self._create_appointment_events(appointment)
        
        elif action == "update":
            # Check if events exist. If not, and it's now 'accepted', create them.
            query = select(CalendarEvent).where(CalendarEvent.appointment_id == appointment.id)
            result = await self.db.execute(query)
            existing = result.scalars().all()
            
            if not existing and appointment.status == "accepted":
                await self._create_appointment_events(appointment)
            else:
                await self._update_appointment_events(appointment)
        
        elif action == "cancel":
            await self._cancel_appointment_events(appointment)
    
    async def _create_appointment_events(self, appointment: Appointment) -> None:
        """Create calendar events for both patient and doctor"""
        # Get users' organization IDs
        from app.models.user import User
        from app.core.security import pii_encryption  # Import the decryption utility
        
        patient_query = select(User).where(User.id == appointment.patient_id)
        doctor_query = select(User).where(User.id == appointment.doctor_id)
        
        patient_result = await self.db.execute(patient_query)
        doctor_result = await self.db.execute(doctor_query)
        
        patient = patient_result.scalar_one_or_none()
        doctor = doctor_result.scalar_one_or_none()
        
        if not patient or not doctor:
            return
        
        # --- NEW: Decrypt the names safely ---
        try:
            patient_name = pii_encryption.decrypt(patient.full_name)
        except Exception:
            patient_name = "Patient"
            
        try:
            doctor_name = pii_encryption.decrypt(doctor.full_name)
        except Exception:
            doctor_name = "Doctor"
        # -------------------------------------
        
        # Determine event title based on role using DECRYPTED names
        patient_title = f"Appointment with Dr. {doctor_name}"
        doctor_title = f"Appointment with {patient_name}"
        
        # Ensure times are localized to organization timezone if requested_date is naive
        # We assume requested_date in DB is UTC or naive representing UTC.
        start_time = appointment.requested_date
        if start_time.tzinfo is None:
             start_time = pytz.UTC.localize(start_time)
        
        # Create event for patient
        patient_event = CalendarEvent(
            user_id=appointment.patient_id,
            organization_id=patient.organization_id,
            event_type="appointment",
            appointment_id=appointment.id,
            title=patient_title,
            description=appointment.reason,
            start_time=start_time,
            end_time=start_time + timedelta(minutes=30),  # Default 30 min
            all_day=False,
            color="#3B82F6",  # Blue for appointments
            status="scheduled"
        )
        
        # Create event for doctor
        doctor_event = CalendarEvent(
            user_id=appointment.doctor_id,
            organization_id=doctor.organization_id,
            event_type="appointment",
            appointment_id=appointment.id,
            title=doctor_title,
            description=appointment.reason,
            start_time=start_time,
            end_time=start_time + timedelta(minutes=30),
            all_day=False,
            color="#3B82F6",
            status="scheduled"
        )
        
        self.db.add(patient_event)
        self.db.add(doctor_event)
        await self.db.flush()
    
    async def _update_appointment_events(self, appointment: Appointment) -> None:
        """Update calendar events linked to an appointment"""
        query = select(CalendarEvent).where(
            CalendarEvent.appointment_id == appointment.id
        )
        result = await self.db.execute(query)
        events = result.scalars().all()
        
        for event in events:
            event.start_time = appointment.requested_date
            event.end_time = appointment.requested_date + timedelta(minutes=30)
            event.description = appointment.reason
            
            # Update status based on appointment status
            if appointment.status == "accepted":
                event.status = "scheduled"
            elif appointment.status == "completed":
                event.status = "completed"
            elif appointment.status in ["declined", "cancelled", "rejected"]:
                event.status = "cancelled"
            
            event.updated_at = datetime.utcnow()
        
        await self.db.flush()
    
    async def _cancel_appointment_events(self, appointment: Appointment) -> None:
        """Mark calendar events as cancelled"""
        query = select(CalendarEvent).where(
            CalendarEvent.appointment_id == appointment.id
        )
        result = await self.db.execute(query)
        events = result.scalars().all()
        
        for event in events:
            event.status = "cancelled"
            event.updated_at = datetime.utcnow()
        
        await self.db.flush()
    
    async def sync_task_to_calendar(
        self,
        task: Task,
        action: str  # "create", "update", "delete"
    ) -> None:
        """
        Sync a task to a calendar event (only if task has due_date)
        
        Args:
            task: Task object
            action: Action to perform ("create", "update", "delete")
        """
        if action == "create" and task.due_date:
            await self._create_task_event(task)
        
        elif action == "update":
            await self._update_task_event(task)
        
        elif action == "delete":
            await self._delete_task_event(task)
    
    async def _create_task_event(self, task: Task) -> None:
        """Create a calendar event for a task"""
        if not task.due_date:
            return
        
        # Get user's organization ID
        from app.models.user import User
        user_query = select(User).where(User.id == task.doctor_id)
        user_result = await self.db.execute(user_query)
        user = user_result.scalar_one_or_none()
        
        if not user:
            return
        
        # Determine color based on priority
        color = "#EF4444" if task.priority == "urgent" else "#F59E0B"  # Red for urgent, orange for normal
        
        event = CalendarEvent(
            user_id=task.doctor_id,
            organization_id=user.organization_id,
            event_type="task",
            task_id=task.id,
            title=f"Task: {task.title}",
            description=task.description,
            start_time=task.due_date,
            end_time=task.due_date + timedelta(hours=1),  # Default 1 hour
            all_day=False,
            color=color,
            status="scheduled" if task.status == "pending" else "completed"
        )
        
        self.db.add(event)
        await self.db.flush()
    
    async def _update_task_event(self, task: Task) -> None:
        """Update calendar event linked to a task"""
        query = select(CalendarEvent).where(
            CalendarEvent.task_id == task.id
        )
        result = await self.db.execute(query)
        event = result.scalar_one_or_none()
        
        if not event:
            # If no event exists and task now has due_date, create one
            if task.due_date:
                await self._create_task_event(task)
            return
        
        # Update event if task still has due_date
        if task.due_date:
            event.title = f"Task: {task.title}"
            event.description = task.description
            event.start_time = task.due_date
            event.end_time = task.due_date + timedelta(hours=1)
            event.status = "scheduled" if task.status == "pending" else "completed"
            event.color = "#EF4444" if task.priority == "urgent" else "#F59E0B"
            event.updated_at = datetime.utcnow()
        else:
            # If task no longer has due_date, delete the calendar event
            await self.db.delete(event)
        
        await self.db.flush()
    
    async def _delete_task_event(self, task: Task) -> None:
        """Delete calendar event linked to a task"""
        query = select(CalendarEvent).where(
            CalendarEvent.task_id == task.id
        )
        result = await self.db.execute(query)
        event = result.scalar_one_or_none()
        
        if event:
            await self.db.delete(event)
            await self.db.flush()
    
    async def _get_org_tz(self, user_id: UUID):
        import pytz
        from app.models.user import User, Organization
        
        # Query the Organization's timezone linked to the user
        query = select(Organization.timezone).join(
            User, User.organization_id == Organization.id
        ).where(User.id == user_id)
        
        result = await self.db.execute(query)
        org_tz_str = result.scalar_one_or_none()
        
        try:
            return pytz.timezone(org_tz_str or "UTC")
        except Exception:
            return pytz.UTC

    async def get_day_view(self, user_id: UUID, target_date: date, organization_id: Optional[UUID] = None) -> List[CalendarEvent]:
        """
        Get all events for a specific day.
        If organization_id is provided, returns all organization events for that day.
        """
<<<<<<< Updated upstream
        tz = await self._get_org_tz(user_id)
        
        # Localize target date boundaries and convert to UTC for DB queries
        local_start = tz.localize(datetime.combine(target_date, datetime.min.time()))
        local_end = tz.localize(datetime.combine(target_date, datetime.max.time()))
        
        import pytz
        start_datetime = local_start.astimezone(pytz.UTC)
        end_datetime = local_end.astimezone(pytz.UTC)
=======
        tz = await self._get_org_tz(user_id)
        
        # Localize target date boundaries and convert to UTC for DB queries
        # tz is a pytz timezone object (returned by _get_org_tz)
        local_start = tz.localize(datetime.combine(target_date, datetime.min.time()))
        local_end = tz.localize(datetime.combine(target_date, datetime.max.time()))
        
        import pytz
        start_datetime = local_start.astimezone(pytz.UTC)
        end_datetime = local_end.astimezone(pytz.UTC)
>>>>>>> Stashed changes
        
        if organization_id:
            return await self.get_organization_events(organization_id, start_datetime, end_datetime)
        
        return await self.get_events_by_date_range(user_id, start_datetime, end_datetime)
    
    async def get_month_view(self, user_id: UUID, year: int, month: int, organization_id: Optional[UUID] = None) -> dict:
        """
        Get summary of all days in a month with event counts.
        If organization_id is provided, returns counts for the entire organization.
        """
        import pytz
        tz = await self._get_org_tz(user_id)
        
        # Calculate month range using user's timezone mapped to UTC
        local_start_date = tz.localize(datetime(year, month, 1))
        
        if month == 12:
            local_end_date = tz.localize(datetime(year + 1, 1, 1)) - timedelta(seconds=1)
        else:
            local_end_date = tz.localize(datetime(year, month + 1, 1)) - timedelta(seconds=1)
            
        start_date = local_start_date.astimezone(pytz.UTC)
        end_date = local_end_date.astimezone(pytz.UTC)
        
        # Get all events for the month
        if organization_id:
            events = await self.get_organization_events(organization_id, start_date, end_date)
        else:
            events = await self.get_events_by_date_range(user_id, start_date, end_date)
        
        # Group events by day based on the user's localized time
        days_summary = {}
        for event in events:
            ev_start = event.start_time
            if ev_start.tzinfo is None:
                ev_start = pytz.UTC.localize(ev_start)
            local_ev_start = ev_start.astimezone(tz)
            
            day = local_ev_start.day
            if day not in days_summary:
                days_summary[day] = {
                    "day": day,
                    "event_count": 0,
                    "has_appointments": False,
                    "has_tasks": False,
                    "has_custom_events": False
                }
            
            days_summary[day]["event_count"] += 1
            if event.event_type == "appointment":
                days_summary[day]["has_appointments"] = True
            elif event.event_type == "task":
                days_summary[day]["has_tasks"] = True
            elif event.event_type == "custom":
                days_summary[day]["has_custom_events"] = True
        
        return {
            "year": year,
            "month": month,
            "days": list(days_summary.values()),
            "total_events": len(events)
        }

    async def get_organization_events(
        self,
        organization_id: UUID,
        start_date: datetime,
        end_date: datetime,
        event_type: Optional[str] = None,
        doctor_id: Optional[UUID] = None,
        visit_type: Optional[str] = None # "video" or "in-person"
    ) -> List[CalendarEvent]:
        """
        Get all calendar events for an entire organization within a date range.
        Used for the department-wide Shift Schedule UI.
        """
        from sqlalchemy.orm import selectinload
        
        query = select(CalendarEvent).where(
            and_(
                CalendarEvent.organization_id == organization_id,
                CalendarEvent.start_time >= start_date,
                CalendarEvent.start_time <= end_date
            )
        ).options(
            selectinload(CalendarEvent.user),
            selectinload(CalendarEvent.appointment).selectinload(Appointment.doctor),
            selectinload(CalendarEvent.appointment).selectinload(Appointment.patient),
            selectinload(CalendarEvent.task)
        )
        
        if event_type:
            query = query.where(CalendarEvent.event_type == event_type)
        
        if doctor_id:
            query = query.where(CalendarEvent.user_id == doctor_id)
            
        if visit_type:
            # Join with Appointment to filter by visit type (video vs in-person)
            # Since visit_type is not a column, we use meet_link as proxy
            query = query.join(CalendarEvent.appointment)
            if visit_type == "video":
                query = query.where(Appointment.meet_link.isnot(None))
            else:
                query = query.where(Appointment.meet_link.is_(None))
        
        query = query.order_by(CalendarEvent.start_time.asc())
        
        result = await self.db.execute(query)
        return result.scalars().all()