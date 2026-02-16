"""
Integration tests for Calendar System API

Tests cover:
1. Calendar event CRUD operations
2. Bidirectional appointment sync (patient + doctor)
3. Task sync with calendar
4. Day/Month views
5. Role-based access control
6. Date range filtering
"""
import pytest
from datetime import datetime, timedelta, date
from uuid import uuid4


class TestCalendarEventCRUD:
    """Test basic calendar event CRUD operations"""
    
    @pytest.mark.asyncio
    async def test_create_custom_event(self, test_client, doctor_token, doctor_user):
        """Doctor can create a custom calendar event"""
        event_data = {
            "title": "Team Meeting",
            "description": "Weekly sync with medical team",
            "start_time": (datetime.utcnow() + timedelta(days=1)).isoformat() + "Z",
            "end_time": (datetime.utcnow() + timedelta(days=1, hours=1)).isoformat() + "Z",
            "all_day": False,
            "color": "#10B981",
            "reminder_minutes": 15
        }
        
        response = await test_client.post(
            "/api/v1/calendar/events",
            json=event_data,
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == event_data["title"]
        assert data["event_type"] == "custom"
        assert data["user_id"] == str(doctor_user.id)
        assert data["color"] == "#10B981"
    
    @pytest.mark.asyncio
    async def test_list_calendar_events(self, test_client, doctor_token):
        """Doctor can list their calendar events"""
        start = datetime.utcnow()
        end = start + timedelta(days=30)
        
        response = await test_client.get(
            f"/api/v1/calendar/events?start_date={start.isoformat()}Z&end_date={end.isoformat()}Z",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_get_single_calendar_event(self, test_client, doctor_token, doctor_user):
        """Doctor can retrieve a single calendar event"""
        # Create event first
        event_data = {
            "title": "Personal Event",
            "start_time": (datetime.utcnow() + timedelta(days=2)).isoformat() + "Z",
            "end_time": (datetime.utcnow() + timedelta(days=2, hours=2)).isoformat() + "Z",
            "all_day": False
        }
        
        create_response = await test_client.post(
            "/api/v1/calendar/events",
            json=event_data,
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        event_id = create_response.json()["id"]
        
        # Retrieve it
        response = await test_client.get(
            f"/api/v1/calendar/events/{event_id}",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == event_id
        assert data["title"] == event_data["title"]
    
    @pytest.mark.asyncio
    async def test_update_custom_event(self, test_client, doctor_token):
        """Doctor can update their custom calendar event"""
        # Create event
        event_data = {
            "title": "Original Title",
            "start_time": (datetime.utcnow() + timedelta(days=3)).isoformat() + "Z",
            "end_time": (datetime.utcnow() + timedelta(days=3, hours=1)).isoformat() + "Z",
            "all_day": False
        }
        
        create_response = await test_client.post(
            "/api/v1/calendar/events",
            json=event_data,
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        event_id = create_response.json()["id"]
        
        # Update it
        update_data = {
            "title": "Updated Title",
            "color": "#EF4444"
        }
        
        response = await test_client.put(
            f"/api/v1/calendar/events/{event_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["color"] == "#EF4444"
    
    @pytest.mark.asyncio
    async def test_delete_custom_event(self, test_client, doctor_token):
        """Doctor can delete their custom calendar event"""
        # Create event
        event_data = {
            "title": "Event to Delete",
            "start_time": (datetime.utcnow() + timedelta(days=4)).isoformat() + "Z",
            "end_time": (datetime.utcnow() + timedelta(days=4, hours=1)).isoformat() + "Z",
            "all_day": False
        }
        
        create_response = await test_client.post(
            "/api/v1/calendar/events",
            json=event_data,
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        event_id = create_response.json()["id"]
        
        # Delete it
        response = await test_client.delete(
            f"/api/v1/calendar/events/{event_id}",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        
        assert response.status_code == 204
        
        # Verify it's gone
        get_response = await test_client.get(
            f"/api/v1/calendar/events/{event_id}",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        assert get_response.status_code == 404


class TestAppointmentSync:
    """Test bidirectional appointment-to-calendar synchronization"""
    
    @pytest.mark.asyncio
    async def test_appointment_creates_calendar_events_for_both_users(
        self, test_client, patient_token, doctor_token, doctor_user, patient_user
    ):
        """When patient books appointment, both patient and doctor get calendar events"""
        appointment_time = datetime.utcnow() + timedelta(days=5)
        
        # Patient creates appointment
        appointment_data = {
            "doctor_id": str(doctor_user.id),
            "requested_date": appointment_time.isoformat() + "Z",
            "reason": "Annual checkup"
        }
        
        apt_response = await test_client.post(
            "/api/v1/appointments",
            json=appointment_data,
            headers={"Authorization": f"Bearer {patient_token}"}
        )
        
        assert apt_response.status_code == 201
        appointment_id = apt_response.json()["id"]
        
        # Check patient's calendar
        start = appointment_time - timedelta(hours=1)
        end = appointment_time + timedelta(hours=1)
        
        patient_calendar = await test_client.get(
            f"/api/v1/calendar/events?start_date={start.isoformat()}Z&end_date={end.isoformat()}Z",
            headers={"Authorization": f"Bearer {patient_token}"}
        )
        
        patient_events = patient_calendar.json()
        assert len(patient_events) >= 1
        patient_apt_event = next((e for e in patient_events if e["appointment_id"] == appointment_id), None)
        assert patient_apt_event is not None
        assert patient_apt_event["event_type"] == "appointment"
        assert "Appointment with" in patient_apt_event["title"]
        
        # Check doctor's calendar
        doctor_calendar = await test_client.get(
            f"/api/v1/calendar/events?start_date={start.isoformat()}Z&end_date={end.isoformat()}Z",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        
        doctor_events = doctor_calendar.json()
        assert len(doctor_events) >= 1
        doctor_apt_event = next((e for e in doctor_events if e["appointment_id"] == appointment_id), None)
        assert doctor_apt_event is not None
        assert doctor_apt_event["event_type"] == "appointment"
        assert "Appointment with" in doctor_apt_event["title"]
    
    @pytest.mark.asyncio
    async def test_appointment_cancellation_updates_calendar(
        self, test_client, patient_token, doctor_token, doctor_user
    ):
        """When appointment is cancelled, calendar events are marked as cancelled"""
        appointment_time = datetime.utcnow() + timedelta(days=6)
        
        # Create appointment
        appointment_data = {
            "doctor_id": str(doctor_user.id),
            "requested_date": appointment_time.isoformat() + "Z",
            "reason": "Consultation"
        }
        
        apt_response = await test_client.post(
            "/api/v1/appointments",
            json=appointment_data,
            headers={"Authorization": f"Bearer {patient_token}"}
        )
        appointment_id = apt_response.json()["id"]
        
        # Doctor cancels appointment
        status_update = {
            "status": "cancelled",
            "doctor_notes": "Emergency conflict"
        }
        
        await test_client.put(
            f"/api/v1/appointments/{appointment_id}/status",
            json=status_update,
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        
        # Check patient's calendar - event should be cancelled
        start = appointment_time - timedelta(hours=1)
        end = appointment_time + timedelta(hours=1)
        
        patient_calendar = await test_client.get(
            f"/api/v1/calendar/events?start_date={start.isoformat()}Z&end_date={end.isoformat()}Z",
            headers={"Authorization": f"Bearer {patient_token}"}
        )
        
        patient_events = patient_calendar.json()
        patient_apt_event = next((e for e in patient_events if e["appointment_id"] == appointment_id), None)
        assert patient_apt_event["status"] == "cancelled"
    
    @pytest.mark.asyncio
    async def test_cannot_update_appointment_event_via_calendar_api(
        self, test_client, patient_token, doctor_user
    ):
        """Users cannot update appointment-linked calendar events directly"""
        appointment_time = datetime.utcnow() + timedelta(days=7)
        
        # Create appointment
        appointment_data = {
            "doctor_id": str(doctor_user.id),
            "requested_date": appointment_time.isoformat() + "Z",
            "reason": "Follow-up"
        }
        
        apt_response = await test_client.post(
            "/api/v1/appointments",
            json=appointment_data,
            headers={"Authorization": f"Bearer {patient_token}"}
        )
        
        # Get the calendar event
        start = appointment_time - timedelta(hours=1)
        end = appointment_time + timedelta(hours=1)
        
        calendar_response = await test_client.get(
            f"/api/v1/calendar/events?start_date={start.isoformat()}Z&end_date={end.isoformat()}Z",
            headers={"Authorization": f"Bearer {patient_token}"}
        )
        
        events = calendar_response.json()
        apt_event = next((e for e in events if e["event_type"] == "appointment"), None)
        
        # Try to update it via calendar API - should fail
        update_data = {"title": "Hacked Title"}
        
        response = await test_client.put(
            f"/api/v1/calendar/events/{apt_event['id']}",
            json=update_data,
            headers={"Authorization": f"Bearer {patient_token}"}
        )
        
        assert response.status_code == 400
        assert "Cannot update appointment-linked events" in response.json()["detail"]


class TestTaskSync:
    """Test task-to-calendar synchronization"""
    
    @pytest.mark.asyncio
    async def test_task_with_due_date_creates_calendar_event(
        self, test_client, doctor_token
    ):
        """When doctor creates task with due date, calendar event is created"""
        due_date = datetime.utcnow() + timedelta(days=3)
        
        task_data = {
            "title": "Review Lab Results",
            "description": "Patient X bloodwork",
            "due_date": due_date.isoformat() + "Z",
            "priority": "urgent"
        }
        
        task_response = await test_client.post(
            "/api/v1/doctor/tasks",
            json=task_data,
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        
        assert task_response.status_code == 201
        task_id = task_response.json()["id"]
        
        # Check calendar
        start = due_date - timedelta(hours=1)
        end = due_date + timedelta(hours=1)
        
        calendar_response = await test_client.get(
            f"/api/v1/calendar/events?start_date={start.isoformat()}Z&end_date={end.isoformat()}Z",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        
        events = calendar_response.json()
        task_event = next((e for e in events if e["task_id"] == task_id), None)
        assert task_event is not None
        assert task_event["event_type"] == "task"
        assert "Task:" in task_event["title"]
        assert task_event["color"] == "#EF4444"  # Urgent = red
    
    @pytest.mark.asyncio
    async def test_task_without_due_date_no_calendar_event(
        self, test_client, doctor_token
    ):
        """Tasks without due dates don't create calendar events"""
        task_data = {
            "title": "General TODO",
            "description": "No specific deadline",
            "priority": "normal"
        }
        
        task_response = await test_client.post(
            "/api/v1/doctor/tasks",
            json=task_data,
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        
        task_id = task_response.json()["id"]
        
        # Check calendar - should not exist
        start = datetime.utcnow()
        end = start + timedelta(days=30)
        
        calendar_response = await test_client.get(
            f"/api/v1/calendar/events?start_date={start.isoformat()}Z&end_date={end.isoformat()}Z&event_type=task",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        
        events = calendar_response.json()
        task_event = next((e for e in events if e["task_id"] == task_id), None)
        assert task_event is None
    
    @pytest.mark.asyncio
    async def test_task_deletion_removes_calendar_event(
        self, test_client, doctor_token
    ):
        """Deleting a task removes its calendar event"""
        due_date = datetime.utcnow() + timedelta(days=8)
        
        # Create task with due date
        task_data = {
            "title": "Temporary Task",
            "due_date": due_date.isoformat() + "Z",
            "priority": "normal"
        }
        
        task_response = await test_client.post(
            "/api/v1/doctor/tasks",
            json=task_data,
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        task_id = task_response.json()["id"]
        
        # Delete task
        await test_client.delete(
            f"/api/v1/doctor/tasks/{task_id}",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        
        # Verify calendar event is gone
        start = due_date - timedelta(hours=1)
        end = due_date + timedelta(hours=1)
        
        calendar_response = await test_client.get(
            f"/api/v1/calendar/events?start_date={start.isoformat()}Z&end_date={end.isoformat()}Z",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        
        events = calendar_response.json()
        task_event = next((e for e in events if e["task_id"] == task_id), None)
        assert task_event is None


class TestCalendarViews:
    """Test day/month view endpoints"""
    
    @pytest.mark.asyncio
    async def test_day_view(self, test_client, doctor_token):
        """Day view returns all events for a specific day"""
        target_date = date.today() + timedelta(days=10)
        
        # Create event on that day
        event_data = {
            "title": "Day View Test Event",
            "start_time": datetime.combine(target_date, datetime.min.time()).isoformat() + "Z",
            "end_time": (datetime.combine(target_date, datetime.min.time()) + timedelta(hours=1)).isoformat() + "Z",
            "all_day": False
        }
        
        await test_client.post(
            "/api/v1/calendar/events",
            json=event_data,
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        
        # Get day view
        response = await test_client.get(
            f"/api/v1/calendar/day/{target_date.isoformat()}",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["date"] == target_date.isoformat()
        assert "events" in data
        assert "total_count" in data
        assert isinstance(data["events"], list)
    
    @pytest.mark.asyncio
    async def test_month_view(self, test_client, doctor_token):
        """Month view returns summary for entire month"""
        target_year = 2026
        target_month = 3
        
        response = await test_client.get(
            f"/api/v1/calendar/month/{target_year}/{target_month}",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["year"] == target_year
        assert data["month"] == target_month
        assert "days" in data
        assert "total_events" in data
        assert isinstance(data["days"], list)


class TestAccessControl:
    """Test role-based access control"""
    
    @pytest.mark.asyncio
    async def test_user_cannot_access_other_user_events(
        self, test_client, doctor_token, patient_token, doctor_user
    ):
        """Users can only see their own events (tenant isolation)"""
        # Doctor creates event
        event_data = {
            "title": "Private Doctor Event",
            "start_time": (datetime.utcnow() + timedelta(days=15)).isoformat() + "Z",
            "end_time": (datetime.utcnow() + timedelta(days=15, hours=1)).isoformat() + "Z",
            "all_day": False
        }
        
        doctor_event_response = await test_client.post(
            "/api/v1/calendar/events",
            json=event_data,
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        doctor_event_id = doctor_event_response.json()["id"]
        
        # Patient tries to access doctor's event
        response = await test_client.get(
            f"/api/v1/calendar/events/{doctor_event_id}",
            headers={"Authorization": f"Bearer {patient_token}"}
        )
        
        assert response.status_code == 404


class TestEventFiltering:
    """Test event filtering by type and date range"""
    
    @pytest.mark.asyncio
    async def test_filter_events_by_type(self, test_client, doctor_token):
        """Can filter events by event_type"""
        future_date = datetime.utcnow() + timedelta(days=20)
        
        # Create custom event
        custom_event = {
            "title": "Custom Event",
            "start_time": future_date.isoformat() + "Z",
            "end_time": (future_date + timedelta(hours=1)).isoformat() + "Z",
            "all_day": False
        }
        
        await test_client.post(
            "/api/v1/calendar/events",
            json=custom_event,
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        
        # Filter by custom events only
        start = future_date - timedelta(hours=2)
        end = future_date + timedelta(hours=2)
        
        response = await test_client.get(
            f"/api/v1/calendar/events?start_date={start.isoformat()}Z&end_date={end.isoformat()}Z&event_type=custom",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        
        assert response.status_code == 200
        events = response.json()
        # All returned events should be custom type
        for event in events:
            assert event["event_type"] == "custom"
