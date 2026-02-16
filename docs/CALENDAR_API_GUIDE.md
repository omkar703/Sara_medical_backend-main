# Calendar API - Usage Examples

This document provides practical examples for integrating with the Saramedico Calendar API.

## Table of Contents
- [Authentication](#authentication)
- [Create Custom Event](#create-custom-event)
- [List Events](#list-events)
- [Get Day View](#get-day-view)
- [Get Month View](#get-month-view)
- [Update Event](#update-event)
- [Delete Event](#delete-event)
- [Understanding Event Types](#understanding-event-types)
- [Common Use Cases](#common-use-cases)

## Authentication

All calendar endpoints require JWT authentication. Include the bearer token in the Authorization header:

```bash
Authorization: Bearer <your_jwt_token>
```

## Create Custom Event

Create a custom calendar event (available to all user roles).

**Endpoint:** `POST /api/v1/calendar/events`

**Request:**
```json
{
  "title": "Team Meeting",
  "description": "Monthly team sync - discuss Q1 goals",
  "start_time": "2026-02-20T14:00:00Z",
  "end_time": "2026-02-20T15:30:00Z",
  "all_day": false,
  "color": "#10B981",
  "reminder_minutes": 30
}
```

**Response (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "organization_id": "789e4567-e89b-12d3-a456-426614174000",
  "title": "Team Meeting",
  "description": "Monthly team sync - discuss Q1 goals",
  "start_time": "2026-02-20T14:00:00Z",
  "end_time": "2026-02-20T15:30:00Z",
  "all_day": false,
  "event_type": "custom",
  "appointment_id": null,
  "task_id": null,
  "color": "#10B981",
  "reminder_minutes": 30,
  "status": "scheduled",
  "created_at": "2026-02-16T19:30:00Z",
  "updated_at": "2026-02-16T19:30:00Z",
  "metadata": null
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/calendar/events" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Team Meeting",
    "description": "Monthly team sync",
    "start_time": "2026-02-20T14:00:00Z",
    "end_time": "2026-02-20T15:30:00Z",
    "all_day": false,
    "color": "#10B981",
    "reminder_minutes": 30
  }'
```

## List Events

Retrieve calendar events within a date range with optional filtering.

**Endpoint:** `GET /api/v1/calendar/events`

**Query Parameters:**
- `start_date` (required) - ISO 8601 datetime
- `end_date` (required) - ISO 8601 datetime
- `event_type` (optional) - Filter by: `appointment`, `custom`, or `task`

**Example 1: Get all events for the next week**
```bash
curl -X GET "http://localhost:8000/api/v1/calendar/events?start_date=2026-02-16T00:00:00Z&end_date=2026-02-23T23:59:59Z" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Example 2: Get only appointments for today**
```bash
curl -X GET "http://localhost:8000/api/v1/calendar/events?start_date=2026-02-16T00:00:00Z&end_date=2026-02-16T23:59:59Z&event_type=appointment" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
[
  {
    "id": "apt-event-uuid",
    "title": "Appointment with Dr. Smith",
    "description": "Annual checkup",
    "start_time": "2026-02-18T10:00:00Z",
    "end_time": "2026-02-18T10:30:00Z",
    "event_type": "appointment",
    "appointment_id": "appointment-uuid",
    "color": "#3B82F6",
    "status": "scheduled",
    "metadata": {
      "appointment_status": "accepted",
      "zoom_link": "https://zoom.us/j/123456789"
    }
  },
  {
    "id": "custom-event-uuid",
    "title": "Team Meeting",
    "start_time": "2026-02-20T14:00:00Z",
    "end_time": "2026-02-20T15:30:00Z",
    "event_type": "custom",
    "color": "#10B981",
    "status": "scheduled"
  }
]
```

## Get Day View

Get all events for a specific day with summary information.

**Endpoint:** `GET /api/v1/calendar/day/{date}`

**URL Parameter:** `date` in YYYY-MM-DD format

**Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/calendar/day/2026-02-20" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "date": "2026-02-20",
  "events": [
    {
      "id": "event-uuid-1",
      "title": "Morning Appointment",
      "start_time": "2026-02-20T09:00:00Z",
      "end_time": "2026-02-20T09:30:00Z",
      "event_type": "appointment",
      "color": "#3B82F6"
    },
    {
      "id": "event-uuid-2",
      "title": "Team Meeting",
      "start_time": "2026-02-20T14:00:00Z",
      "end_time": "2026-02-20T15:30:00Z",
      "event_type": "custom",
      "color": "#10B981"
    }
  ],
  "total_count": 2
}
```

## Get Month View

Get a summary of all days in a month with event counts.

**Endpoint:** `GET /api/v1/calendar/month/{year}/{month}`

**URL Parameters:**
- `year` - Four-digit year (e.g., 2026)
- `month` - Month number 1-12

**Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/calendar/month/2026/2" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "year": 2026,
  "month": 2,
  "days": [
    {
      "day": 1,
      "event_count": 0,
      "appointment_count": 0,
      "custom_count": 0,
      "task_count": 0
    },
    {
      "day": 16,
      "event_count": 3,
      "appointment_count": 1,
      "custom_count": 1,
      "task_count": 1
    },
    {
      "day": 20,
      "event_count": 2,
      "appointment_count": 1,
      "custom_count": 1,
      "task_count": 0
    }
  ],
  "total_events": 5
}
```

## Update Event

Update a custom calendar event (appointment and task events cannot be updated via calendar API).

**Endpoint:** `PUT /api/v1/calendar/events/{id}`

**Request (Partial Update):**
```json
{
  "title": "Updated Meeting Title",
  "color": "#EF4444",
  "reminder_minutes": 60
}
```

**Response:**
```json
{
  "id": "event-uuid",
  "title": "Updated Meeting Title",
  "description": "Monthly team sync",
  "start_time": "2026-02-20T14:00:00Z",
  "end_time": "2026-02-20T15:30:00Z",
  "color": "#EF4444",
  "reminder_minutes": 60,
  "updated_at": "2026-02-16T20:00:00Z"
}
```

**Important:** You cannot update appointment-linked or task-linked events. Use the respective APIs for those.

## Delete Event

Delete a custom calendar event.

**Endpoint:** `DELETE /api/v1/calendar/events/{id}`

**Response:** 204 No Content

**Example:**
```bash
curl -X DELETE "http://localhost:8000/api/v1/calendar/events/event-uuid" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Important:** You cannot delete appointment-linked or task-linked events. Cancel the appointment or delete the task instead.

## Understanding Event Types & Role Visibility

The calendar system implements strict data isolation. Users only see events relevant to them.

### Role-Based Visibility Matrix

| Event Type | Patient | Doctor | Admin | Hospital |
|------------|---------|--------|-------|----------|
| **Custom** | Only their own | Only their own | Only their own | Only their own |
| **Appointment** | Their appointments | Their appointments | Not visible* | Not visible* |
| **Task** | Not visible | Only their own | Not visible | Not visible |

*\*Admin and Hospital roles currently use the calendar for internal scheduling and management tasks.*

### 1. Appointment Events (Auto-Created)
- **Color:** Blue (`#3B82F6`)
- **Bidirectional:** When an appointment is created, **two** calendar events are generated: one for the patient and one for the doctor.
- **Dynamic Titles:**
  - Patient sees: "Appointment with Dr. [Full Name]"
  - Doctor sees: "Appointment with [Patient Full Name]"
- **Metadata Object:**
  ```json
  "metadata": {
    "appointment_status": "accepted",
    "zoom_link": "https://zoom.us/j/..."
  }
  ```
  *Note: `zoom_link` is null until the appointment is approved.*

### 2. Task Events (Auto-Created)
- **Color:** 
  - Red (`#EF4444`) for urgent tasks
  - Orange (`#F59E0B`) for normal tasks
- **Logic:** Appears only in the creator doctor's calendar on the `due_date`.
- **Status:** Linked to the task status (`pending` or `completed`).

### 3. Custom Events (User-Created)
- **Color:** Fully customizable hex code.
- **Visibility:** Private to the user who created it.
- **Full CRUD:** Support `POST`, `PUT`, `DELETE` via the `/calendar/events` endpoints.

## Metadata Integration

The `metadata` field is crucial for rich frontend displays. It is currently used for **Appointment** events to provide:
1.  **Status Badges**: Use `appointment_status` to show if an appointment is pending, accepted, or cancelled.
2.  **Join Button**: Use `zoom_link` to render a "Join Meeting" button directly in the calendar view or tooltip.

Example of handling in React/JS:
```javascript
function EventTooltip({ event }) {
  const { event_type, metadata } = event;
  
  return (
    <div>
      <h4>{event.title}</h4>
      {event_type === 'appointment' && metadata && (
        <>
          <span className={`badge-${metadata.appointment_status}`}>
            {metadata.appointment_status}
          </span>
          {metadata.zoom_link && (
            <a href={metadata.zoom_link} target="_blank">Join Zoom Meeting</a>
          )}
        </>
      )}
    </div>
  );
}
```

## Common Use Cases

### Use Case 1: Building a Calendar UI

**Goal:** Display a monthly calendar with all events

**Step 1:** Get month summary
```javascript
const response = await fetch(
  'http://localhost:8000/api/v1/calendar/month/2026/2',
  { headers: { 'Authorization': `Bearer ${token}` }}
);
const monthData = await response.json();

// monthData.days gives you event counts per day
// Use this to show indicators on calendar grid
```

**Step 2:** When user clicks a day, get day view
```javascript
const dayResponse = await fetch(
  'http://localhost:8000/api/v1/calendar/day/2026-02-20',
  { headers: { 'Authorization': `Bearer ${token}` }}
);
const dayData = await dayResponse.json();

// dayData.events contains all events for that day
// Render event list or agenda view
```

### Use Case 2: Syncing Appointments to Frontend

**Scenario:** User books an appointment through your app

**Backend automatically:**
1. Creates appointment record
2. Triggers calendar sync
3. Creates calendar events for patient AND doctor

**Frontend should:**
1. After appointment creation succeeds, refresh calendar
2. Query calendar events to show updated schedule

```javascript
// After booking appointment
await bookAppointment(appointmentData);

// Refresh calendar for the appointment date
const calendarEvents = await fetch(
  `http://localhost:8000/api/v1/calendar/events?start_date=${start}&end_date=${end}`,
  { headers: { 'Authorization': `Bearer ${token}` }}
);

// Calendar now includes the new appointment event
```

### Use Case 3: Doctor's Daily Schedule

**Goal:** Show doctor's schedule for today with all appointments and tasks

```javascript
const today = new Date().toISOString().split('T')[0];

const response = await fetch(
  `http://localhost:8000/api/v1/calendar/day/${today}`,
  { headers: { 'Authorization': `Bearer ${doctorToken}` }}
);

const schedule = await response.json();

// Filter and organize events
const appointments = schedule.events.filter(e => e.event_type === 'appointment');
const tasks = schedule.events.filter(e => e.event_type === 'task');
const meetings = schedule.events.filter(e => e.event_type === 'custom');

// Display as timeline or agenda
```

### Use Case 4: Patient's Upcoming Appointments

**Goal:** Show patient their next 5 appointments

```javascript
const now = new Date();
const future = new Date();
future.setMonth(future.getMonth() + 3); // Next 3 months

const response = await fetch(
  `http://localhost:8000/api/v1/calendar/events?`
  + `start_date=${now.toISOString()}&`
  + `end_date=${future.toISOString()}&`
  + `event_type=appointment`,
  { headers: { 'Authorization': `Bearer ${patientToken}` }}
);

const appointments = await response.json();
const upcoming = appointments
  .filter(apt => apt.status !== 'cancelled')
  .slice(0, 5);

// Display appointment cards
```

## Error Handling

### 400 Bad Request - Cannot Update Appointment Event
```json
{
  "detail": "Cannot update appointment-linked events. Use appointment APIs instead."
}
```
**Solution:** Use `PUT /api/v1/appointments/{id}/status` to update appointments.

### 404 Not Found
```json
{
  "detail": "Calendar event not found"
}
```
**Reasons:**
- Event doesn't exist
- Event belongs to another user (tenant isolation)

### 401 Unauthorized
**Reason:** Missing or invalid JWT token

**Solution:** Include valid bearer token in Authorization header.

## Best Practices

1. **Date Ranges:** Keep date ranges reasonable (max 3 months) for performance
2. **Filtering:** Use `event_type` filter when you only need specific event types
3. **Caching:** Calendar data changes frequently; refresh on appointment/task actions
4. **Timezones:** All times are in UTC; convert to user's timezone in frontend
5. **Polling:** Don't poll excessively; refresh on user actions or every 5 minutes
6. **Event Colors:** Respect the color coding system for visual consistency

## Frontend Integration Tips

```javascript
// Utility: Format event for display
function formatEvent(event) {
  const icons = {
    appointment: '🩺',
    task: '✓',
    custom: '📅'
  };
  
  return {
    ...event,
    icon: icons[event.type],
    time: new Date(event.start_time).toLocaleTimeString(),
    canEdit: event.event_type === 'custom'
  };
}

// Utility: Group events by day
function groupByDay(events) {
  return events.reduce((groups, event) => {
    const date = new Date(event.start_time).toISOString().split('T')[0];
    if (!groups[date]) groups[date] = [];
    groups[date].push(event);
    return groups;
  }, {});
}
```

## Support

For issues or questions:
- API Documentation: http://localhost:8000/docs
- Swagger UI: Interactive API testing
- Contact: Technical support team
