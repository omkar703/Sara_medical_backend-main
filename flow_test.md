# End-to-End API Flow Test - SaraMedico Platform

**Purpose**: Golden Path user journey testing for Postman Collection Runner  
**Base URL**: `{{base_url}}` = `http://localhost:8000/api/v1`

---

## Phase 1: Doctor Setup (Dr. Sarah)

### Step 1: Doctor Registration

**POST** `{{base_url}}/auth/register`

**Body:**

```json
{
  "email": "dr.sarah@saramedico.com",
  "password": "Password123!",
  "role": "doctor",
  "first_name": "Sarah",
  "last_name": "Smith",
  "organization_name": "SaraMedico Clinic"
}
```

**Test Checks:**

- ✓ Status: `201 Created`
- ✓ Save `response.user.id` as `{{doctor_id}}`
- ✓ Verify `response.user.role === "doctor"`

---

### Step 2: Doctor Login

**POST** `{{base_url}}/auth/login`

**Body:**

```json
{
  "email": "dr.sarah@saramedico.com",
  "password": "Password123!"
}
```

**Test Checks:**

- ✓ Status: `200 OK`
- ✓ Save `response.access_token` as `{{doctor_token}}`
- ✓ Save `response.user.id` as `{{doctor_id}}`
- ✓ Save `response.user.organization_id` as `{{organization_id}}`

---

### Step 3: Doctor Onboarding - Set Specialty

**PATCH** `{{base_url}}/doctor/profile`

**Headers:**

```
Authorization: Bearer {{doctor_token}}
Content-Type: application/json
```

**Body:**

```json
{
  "specialty": "Cardiology",
  "license_number": "MD-2024-CARDIO-001"
}
```

**Test Checks:**

- ✓ Status: `200 OK`
- ✓ Verify `response.specialty === "Cardiology"`
- ✓ Verify `response.message` contains "updated successfully"

---

## Phase 2: Patient Setup (Rohit)

### Step 4: Patient Registration

**POST** `{{base_url}}/auth/register`

**Body:**

```json
{
  "email": "rohit.patient@gmail.com",
  "password": "SecurePass123!",
  "role": "patient",
  "first_name": "Rohit",
  "last_name": "Kumar",
  "organization_name": "SaraMedico Clinic"
}
```

**Test Checks:**

- ✓ Status: `201 Created`
- ✓ Save `response.user.id` as `{{patient_id}}`
- ✓ Verify `response.user.role === "patient"`

---

### Step 5: Patient Login

**POST** `{{base_url}}/auth/login`

**Body:**

```json
{
  "email": "rohit.patient@gmail.com",
  "password": "SecurePass123!"
}
```

**Test Checks:**

- ✓ Status: `200 OK`
- ✓ Save `response.access_token` as `{{patient_token}}`
- ✓ Save `response.user.id` as `{{patient_id}}`

---

### Step 6: Patient Uploads Medical History (HIPAA-Compliant)

**POST** `{{base_url}}/patient/medical-history`

**Headers:**

```
Authorization: Bearer {{patient_token}}
Content-Type: multipart/form-data
```

**Body (Form Data):**

```
file: [Binary PDF file - "Blood_Test_Results.pdf"]
category: LAB_REPORT
title: Complete Blood Count Results
description: Blood work from January 2026
```

**Test Checks:**

- ✓ Status: `201 Created`
- ✓ Verify `response.file_name === "Blood_Test_Results.pdf"`
- ✓ Verify `response.category === "LAB_REPORT"`
- ✓ Verify `response.presigned_url` starts with `http://` (15-min expiry)
- ✓ Save `response.id` as `{{document_id}}`

---

## Phase 3: Discovery & Booking

### Step 7: Patient Searches for Cardiologist

**GET** `{{base_url}}/doctors/search?specialty=Cardiology`

**Headers:**

```
Authorization: Bearer {{patient_token}}
```

**Test Checks:**

- ✓ Status: `200 OK`
- ✓ Verify `response.results` is an array with length >= 1
- ✓ Verify `response.results[0].specialty === "Cardiology"`
- ✓ Verify `response.results[0].name` contains "Sarah"
- ✓ Save `response.results[0].id` as `{{found_doctor_id}}`
- ✓ Verify `{{found_doctor_id}} === {{doctor_id}}`

---

### Step 8: Patient Books Appointment with Permission Grant

**POST** `{{base_url}}/appointments/request`

**Headers:**

```
Authorization: Bearer {{patient_token}}
Content-Type: application/json
```

**Body:**

```json
{
  "doctor_id": "{{doctor_id}}",
  "requested_date": "2026-02-15T10:00:00Z",
  "reason": "Chest pain consultation",
  "grant_access_to_history": true
}
```

**Test Checks:**

- ✓ Status: `201 Created`
- ✓ Save `response.id` as `{{appointment_id}}`
- ✓ Verify `response.status === "pending"`
- ✓ Verify `response.doctor_id === {{doctor_id}}`
- ✓ Verify `response.patient_id === {{patient_id}}`

---

## Phase 4: Doctor Workflow

### Step 9: Doctor Views Patient Medical Records (Permission-Based Access)

**GET** `{{base_url}}/doctor/patients/{{patient_id}}/documents`

**Headers:**

```
Authorization: Bearer {{doctor_token}}
```

**Test Checks:**

- ✓ Status: `200 OK` (Permission granted via appointment booking)
- ✓ Verify `response` is an array with length >= 1
- ✓ Verify `response[0].file_name === "Blood_Test_Results.pdf"`
- ✓ Verify `response[0].category === "LAB_REPORT"`
- ✓ Verify `response[0].presigned_url` exists and is a valid URL

**HIPAA Compliance Verification:**

- ✓ URL must expire in 15 minutes
- ✓ Access would fail with `403 Forbidden` if permission not granted

---

### Step 10: Doctor Approves Appointment (Zoom Integration)

**POST** `{{base_url}}/appointments/{{appointment_id}}/approve`

**Headers:**

```
Authorization: Bearer {{doctor_token}}
Content-Type: application/json
```

**Body:**

```json
{
  "appointment_time": "2026-02-15T10:30:00Z",
  "doctor_notes": "Please bring previous cardiac reports if available"
}
```

**Test Checks:**

- ✓ Status: `200 OK`
- ✓ Verify `response.status === "accepted"`
- ✓ Verify `response.meeting_id` exists (Zoom meeting ID)
- ✓ Verify `response.join_url` starts with `https://zoom.us/j/`
- ✓ Verify `response.start_url` starts with `https://zoom.us/s/`
- ✓ Save `response.meeting_id` as `{{zoom_meeting_id}}`
- ✓ Save `response.join_url` as `{{zoom_join_url}}`

**Zoom Integration Verification:**

- ✓ Meeting created using credentials from `.env` (ZOOM_CLIENT_ID, ZOOM_CLIENT_SECRET)
- ✓ Patient can use `{{zoom_join_url}}` to join
- ✓ Doctor can use `response.start_url` to start meeting

---

### Step 11: Doctor Checks Activity Feed

**GET** `{{base_url}}/doctor/activity`

**Headers:**

```
Authorization: Bearer {{doctor_token}}
```

**Test Checks:**

- ✓ Status: `200 OK`
- ✓ Verify response contains "Appointment Scheduled" activity
- ✓ Verify activity includes zoom_link in extra_data

---

## Phase 5: AI Handoff (Future Phase)

### Step 12: Doctor Submits Patient Data to AI Queue

**POST** `{{base_url}}/doctor/ai/contribute`

**Headers:**

```
Authorization: Bearer {{doctor_token}}
Content-Type: application/json
```

**Body:**

```json
{
  "patient_id": "{{patient_id}}",
  "data_payload": {
    "file_ids": ["{{document_id}}"],
    "notes": "Patient presenting with chest pain. Please analyze ECG and blood work.",
    "analysis_type": "cardiac_risk_assessment"
  },
  "request_type": "diagnosis_assist"
}
```

**Test Checks:**

- ✓ Status: `201 Created`
- ✓ Verify `response.status === "pending"`
- ✓ Save `response.queue_id` as `{{ai_queue_id}}`
- ✓ Verify patient data is tagged with `{{patient_id}}` for privacy compliance

---

## Verification Summary

### Security & HIPAA Compliance

- ✅ File encryption at rest (MinIO)
- ✅ Presigned URLs with 15-minute expiration
- ✅ Permission-based access (403 without grant)
- ✅ Audit logging on all sensitive operations

### Data Flow Integrity

- ✅ Doctor ID tracked from registration → profile → search result
- ✅ Patient ID tracked from registration → upload → appointment
- ✅ Appointment ID used for approval and Zoom generation
- ✅ Document ID passed to AI queue

### Integration Points

- ✅ Zoom API (Server-to-Server OAuth)
- ✅ MinIO (S3-compatible storage)
- ✅ PostgreSQL (with pgvector extension)
- ✅ Redis (session management)

### Critical Variable Flow

```
{{doctor_token}} → Profile Update → Search Discovery
{{patient_token}} → File Upload → Appointment Booking → Permission Grant
{{appointment_id}} → Approval → Zoom Meeting Creation
{{patient_id}} + {{document_id}} → AI Queue (Future Processing)
```

---

## Notes for Postman Collection Runner

1. **Environment Variables**: Set `{{base_url}}` to `http://localhost:8000/api/v1` before running
2. **Sequential Execution**: Tests must run in order (1-12) due to dependencies
3. **Token Management**: Tokens are automatically extracted and reused via Tests scripts
4. **File Upload**: For Step 6, use a sample PDF file in the form-data body
5. **Zoom Verification**: Meeting links can be clicked to verify real Zoom room creation

**Expected Total Time**: ~15-20 seconds for full flow execution
