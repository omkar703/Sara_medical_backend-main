
from typing import List, Optional
from uuid import UUID
from datetime import datetime, date, timedelta
from sqlalchemy import select, and_, extract, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calendar_event import CalendarEvent
from app.models.appointment import Appointment
from app.models.task import Task
from app.schemas.calendar import CalendarEventCreate


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
            selectinload(CalendarEvent.appointment),
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
            selectinload(CalendarEvent.appointment),
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
        if action == "create":
            # Create calendar events for both patient and doctor
            await self._create_appointment_events(appointment)
        
        elif action == "update":
            # Update existing calendar events
            await self._update_appointment_events(appointment)
        
        elif action == "cancel":
            # Mark calendar events as cancelled
            await self._cancel_appointment_events(appointment)
    
    async def _create_appointment_events(self, appointment: Appointment) -> None:
        """Create calendar events for both patient and doctor"""
        # Get users' organization IDs
        from app.models.user import User
        
        patient_query = select(User).where(User.id == appointment.patient_id)
        doctor_query = select(User).where(User.id == appointment.doctor_id)
        
        patient_result = await self.db.execute(patient_query)
        doctor_result = await self.db.execute(doctor_query)
        
        patient = patient_result.scalar_one_or_none()
        doctor = doctor_result.scalar_one_or_none()
        
        if not patient or not doctor:
            return
        
        # Determine event title based on role
        patient_title = f"Appointment with Dr. {doctor.full_name}"
        doctor_title = f"Appointment with {patient.full_name}"
        
        # Create event for patient
        patient_event = CalendarEvent(
            user_id=appointment.patient_id,
            organization_id=patient.organization_id,
            event_type="appointment",
            appointment_id=appointment.id,
            title=patient_title,
            description=appointment.reason,
            start_time=appointment.requested_date,
            end_time=appointment.requested_date + timedelta(minutes=30),  # Default 30 min
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
            start_time=appointment.requested_date,
            end_time=appointment.requested_date + timedelta(minutes=30),
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
            elif appointment.status in ["declined", "cancelled"]:
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
    
    async def get_day_view(self, user_id: UUID, target_date: date) -> List[CalendarEvent]:
        """
        Get all events for a specific day
        
        Args:
            user_id: User UUID
            target_date: Date to get events for
        
        Returns:
            List of CalendarEvent objects for that day
        """
        start_datetime = datetime.combine(target_date, datetime.min.time())
        end_datetime = datetime.combine(target_date, datetime.max.time())
        
        return await self.get_events_by_date_range(user_id, start_datetime, end_datetime)
    
    async def get_month_view(self, user_id: UUID, year: int, month: int) -> dict:
        """
        Get summary of all days in a month with event counts
        
        Args:
            user_id: User UUID
            year: Year (e.g., 2024)
            month: Month (1-12)
        
        Returns:
            Dictionary with day-by-day event summary
        """
        # Get first and last day of month
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(seconds=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(seconds=1)
        
        # Get all events for the month
        events = await self.get_events_by_date_range(user_id, start_date, end_date)
        
        # Group events by day
        days_summary = {}
        for event in events:
            day = event.start_time.day
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
