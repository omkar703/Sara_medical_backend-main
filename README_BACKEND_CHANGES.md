# Backend Changes: Doctor Appointment Creation

## Schema Changes
The `appointments` table was updated to support appointments initiated by doctors.
- **Added Column:** `created_by` (VARCHAR(50), default='patient', NOT NULL)
- **Added Column:** `scheduled_at` (TIMESTAMPTZ, nullable)
- **Updated Enum:** `appointment_status` ENUM now includes `'rejected'` value.

## New API Endpoint
**POST** `/api/v1/appointments/doctor-create`

**Description:** Allows a doctor to create an appointment request for a patient. The initial status of the appointment is set to `pending` and the request is sent to the patient.

### Request Body (`DoctorAppointmentCreate`)
```json
{
  "patient_id": "uuid-of-patient",
  "requested_date": "2026-04-01T10:00:00Z",
  "reason": "Follow-up consultation"
}
```

### Response (`AppointmentResponse`)
```json
{
  "id": "uuid-of-appointment",
  "doctor_id": "uuid-of-doctor",
  "patient_id": "uuid-of-patient",
  "requested_date": "2026-04-01T10:00:00Z",
  "reason": "Follow-up consultation",
  "status": "pending",
  "doctor_name": "Dr. John Doe",
  "patient_name": "Jane Smith",
  "created_at": "...",
  "updated_at": "..."
}
```

## Existing API Updates
- **PUT/PATCH** `/api/v1/appointments/{id}/status`
  - Added authorization check to allow patients to accept or decline appointment requests created by doctors. 
  - Patients cannot accept their own requests (enforced via `created_by` column verification).

## Full Flow (Doctor -> Patient -> Approval)
1. **Initiation:** The Doctor uses the dashboard to schedule an appointment. A `POST` request is sent to `/api/v1/appointments/doctor-create`.
2. **Pending State:** The server creates an `Appointment` record with `status="pending"` and `created_by="doctor"`. Calendar events are synced in a "proposed" state and a notification is dispatched to the patient.
3. **Patient Action:** The Patient logs into their dashboard and sees the incoming request. They choose to Accept or Decline the appointment.
4. **Approval/Rejection:**
   - **Accept:** The patient calls `PUT /api/v1/appointments/{id}/status` with `status="accepted"`. Calendar events finalize. (Note: standard Google Meet linked workflow can trigger if the hospital uses direct generation upon patient acceptance, reusing existing logic).
   - **Decline:** The patient calls the status update endpoint with `status="rejected"` or `declined`. Calendar events are removed or marked canceled.
5. **Sync Everywhere:** Updates correctly reflect in metrics, dashboard cards, tasks, calendars (synchronizing "accepted" requests into meetings), and notification workflows.

## Migration Steps
1. Navigate to the backend directory (`d:\SaraMedico\Sara_medical_backend-main`).
2. Run the provided database alteration script to apply the schema changes manually to your Postgres database:
   ```bash
   python alter_db2.py
   ```
   *Alternative:* If you manage migrations via Alembic or direct PSQL access, you can run the following SQL explicitly:
   ```sql
   ALTER TABLE appointments ADD COLUMN created_by VARCHAR(50) DEFAULT 'patient' NOT NULL;
   ALTER TABLE appointments ADD COLUMN scheduled_at TIMESTAMPTZ;
   ALTER TYPE appointment_status ADD VALUE 'rejected';
   ```
3. Restart the backend FastAPI server to load the new `/api/v1/appointments/doctor-create` route and updated schema dependencies.
