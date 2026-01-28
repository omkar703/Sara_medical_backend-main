# Saramedico: Frontend Integration Guidebook

This guide contains verified end-to-end flows and JSON payloads for the Saramedico platform. Use these to test your frontend integration or via Postman.

---

## 🔐 1. Authentication & Security

The platform uses JWT-based authentication. Most endpoints require the `Authorization: Bearer <token>` header.

### A. Registration

**Endpoint:** `POST /api/v1/auth/register`
**Payload:**

```json
{
  "email": "james.wilson@test.com",
  "password": "Password123!",
  "first_name": "James",
  "last_name": "Wilson",
  "organization_name": "Princeton Clinic",
  "role": "patient",
  "phone": "+15551234567",
  "date_of_birth": "1980-05-15"
}
```

### B. Login

**Endpoint:** `POST /api/v1/auth/login`
**Payload:**

```json
{
  "email": "james.wilson@test.com",
  "password": "Password123!"
}
```

**Success Response:**

```json
{
  "success": true,
  "access_token": "eyJhbG...",
  "token_type": "bearer",
  "user": {
    "id": "4fbfabbf-1d73-4bd5-95f8-3c5abe58f336",
    "name": "James Wilson",
    "role": "patient",
    "organization_id": "..."
  }
}
```

---

## 🏥 2. End-to-End Clinical Flow: Appointment to Zoom Call

This flow describes how a patient finds a doctor, requests an appointment, and how the doctor starts a video call.

### Step 1: Patient Searches for Doctor

**Endpoint:** `GET /api/v1/doctors/search?query=Gregory`
**Response:**

```json
{
  "results": [
    {
      "id": "dfffa599-be1e-4be1-b9dc-c2861d4b6d39",
      "name": "Gregory House",
      "specialty": "Diagnostic Medicine",
      "photo_url": "..."
    }
  ]
}
```

### Step 2: Patient Requests Appointment

**Endpoint:** `POST /api/v1/appointments/request`
**Payload:**

```json
{
  "doctor_id": "dfffa599-be1e-4be1-b9dc-c2861d4b6d39",
  "requested_date": "2026-02-01T14:00:00Z",
  "reason": "Chronic leg pain, needs diagnosis.",
  "grant_access_to_history": true
}
```

### Step 3: Doctor Accepts Appointment

**Endpoint:** `PATCH /api/v1/appointments/{appointment_id}/status`
**Payload:**

```json
{
  "status": "accepted",
  "doctor_notes": "Case looks interesting. Let's meet."
}
```

### Step 4: Doctor Schedules Video Call (Zoom)

**Endpoint:** `POST /api/v1/consultations`
**Payload:**

```json
{
  "patientId": "4fbfabbf-1d73-4bd5-95f8-3c5abe58f336",
  "scheduledAt": "2026-02-01T14:00:00Z",
  "durationMinutes": 45,
  "notes": "Initial diagnostic consultation."
}
```

**Response (Includes Zoom Links):**

```json
{
  "id": "e8dd5df9...",
  "meetingId": "12345678",
  "joinUrl": "https://zoom.us/j/mock",
  "startUrl": "https://zoom.us/s/mock",
  "status": "scheduled"
}
```

---

## 🤖 3. AI Document Processing & Medical Chat

### Step 1: Patient Uploads Medical Report (e.g. Blood Test)

**Endpoint:** `POST /api/v1/documents/upload`
**Type:** `multipart/form-data`
**Body:** `file: [Binary File]`, `notes: "Latest blood results"`
**Response:**

```json
{
  "success": true,
  "document_id": "7c66994c-0411-44f2-906c-f38cf564d35a",
  "status": "processing"
}
```

### Step 2: Patient Grants AI Permission (Required for AI Analysis)

**Endpoint:** `POST /api/v1/permissions/grant-doctor-access`
**Payload:**

```json
{
  "doctor_id": "dfffa599-be1e-4be1-b9dc-c2861d4b6d39",
  "ai_access_permission": true,
  "access_level": "read_analyze",
  "expiry_days": 30
}
```

### Step 3: Doctor Triggers AI Analysis

**Endpoint:** `POST /api/v1/doctor/ai/process-document`
**Payload:**

```json
{
  "patient_id": "4fbfabbf-1d73-4bd5-95f8-3c5abe58f336",
  "document_id": "7c66994c-0411-44f2-906c-f38cf564d35a"
}
```

### Step 4: Doctor Chats with AI about the Data

**Endpoint:** `POST /api/v1/doctor/ai/chat/doctor`
**Payload:**

```json
{
  "patient_id": "4fbfabbf-1d73-4bd5-95f8-3c5abe58f336",
  "document_id": "7c66994c-0411-44f2-906c-f38cf564d35a",
  "query": "Is there any evidence of vitamin D deficiency in this report?"
}
```

_Note: This endpoint returns a StreamingResponse. The frontend should handle it as an SSE stream._

---

## 🛠 4. Doctor Management

### View Daily Tasks

**Endpoint:** `GET /api/v1/doctor/tasks`

### Update Task Status

**Endpoint:** `PATCH /api/v1/doctor/tasks/{task_id}`
**Payload:**

```json
{
  "status": "completed"
}
```

### View Patient Medical History

**Endpoint:** `GET /api/v1/doctor/patients/{patient_id}/documents`

---

## 💡 Integration Tips

1. **Timezones**: Always send dates in ISO 8601 format (UTC preferred).
2. **UUIDs**: All IDs are standard UUID v4 strings.
3. **Pydantic Validation**: If you receive a `422 Unprocessable Entity`, check that your JSON field names match exactly (e.g., `patientId` vs `patient_id` - the API uses a mix depending on the endpoint spec, refer to this guide).
4. **MFA**: If login returns `mfa_required: true`, the user must provide a code to `POST /api/v1/auth/verify-mfa`.
