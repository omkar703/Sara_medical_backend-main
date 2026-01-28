# SaraMedico Complete API Flow Documentation

**Version:** 2.0  
**Status:** Production Ready  
**Date:** January 2026

---

## 📊 Table of Contents

1. [Patient Journey Flow](#patient-journey-flow)
2. [Doctor Journey Flow](#doctor-journey-flow)
3. [AI Document Processing Flow](#ai-document-processing-flow)
4. [Complete System Interaction](#complete-system-interaction)
5. [Permission-Based Access Control](#permission-based-access)
6. [API Endpoint Categorization](#api-endpoint-categorization)
7. [Common API Flows](#common-api-flows)
8. [Authentication & MFA Flow](#authentication-flow)
9. [Response Status Codes](#response-status-codes)
10. [HIPAA Compliance](#hipaa-compliance)

---

## 🟢 Patient Journey Flow

### Visual Flow Diagram

```mermaid
graph TD
    A([Patient Starts]) --> B["POST /auth/register<br/>Role: Patient"]
    B --> C["POST /auth/login<br/>Get JWT Token"]
    C --> D["GET /doctors/search<br/>Query: specialty=Cardiology"]
    D --> E["POST /patient/medical-history<br/>Upload Medical Documents"]
    E --> F["POST /appointments/request<br/>doctor_id, requested_date"]
    F --> G["GET /appointments<br/>Check Status"]
    G --> H{Appointment<br/>Approved?}
    H -->|No| I["Status: PENDING<br/>Wait for Doctor"]
    H -->|Yes| J["Status: APPROVED<br/>Receive Zoom Link"]
    I --> G
    J --> K["Join Zoom Meeting<br/>via join_url"]
    K --> L["POST /auth/logout<br/>End Session"]
    L --> M([Patient Ends])

    style B fill:#90EE90
    style C fill:#90EE90
    style E fill:#87CEEB
    style F fill:#FFD700
    style J fill:#98FB98
    style K fill:#FF69B4
```

### Patient API Endpoint Sequence

1. **Register as Patient**

   ```
   POST /api/v1/auth/register
   Role: patient
   ```

2. **Login**

   ```
   POST /api/v1/auth/login
   Returns: access_token, refresh_token
   ```

3. **Search for Doctors**

   ```
   GET /api/v1/doctors/search?specialty=Cardiology&city=NewYork
   Returns: List of doctors matching criteria
   ```

4. **Upload Medical Documents**

   ```
   POST /api/v1/patient/medical-history
   Category: LAB_REPORT, IMAGING, PRESCRIPTION, DISCHARGE_SUMMARY
   Upload 5+ documents
   ```

5. **Request Appointment**

   ```
   POST /api/v1/appointments/request
   Parameters:
     - doctor_id: UUID of selected doctor
     - requested_date: ISO 8601 datetime
     - reason: Reason for appointment
     - grant_access_to_history: true (allows doctor to view documents)
   ```

6. **Check Appointment Status**

   ```
   GET /api/v1/appointments
   Returns: List of appointments with status
   Status values: PENDING, APPROVED, DECLINED, COMPLETED
   ```

7. **Join Video Meeting**

   ```
   When approved, use join_url provided in appointment response
   Join Zoom meeting for consultation
   ```

8. **Logout**
   ```
   POST /api/v1/auth/logout
   Invalidates refresh_token
   ```

---

## 👨‍⚕️ Doctor Journey Flow

### Visual Flow Diagram

```mermaid
graph TD
    A([Doctor Starts]) --> B["POST /auth/register<br/>Role: Doctor<br/>Specialty, License"]
    B --> C["POST /auth/login<br/>Get JWT Token"]
    C --> D["GET /appointments<br/>View Pending Requests"]
    D --> E{Doctor<br/>Decision}
    E -->|Approve| F["POST /appointments/{id}/approve<br/>Create Zoom Meeting"]
    E -->|Decline| G["PATCH /appointments/{id}/status<br/>Status: DECLINED"]
    F --> H["Zoom Meeting Created<br/>meeting_id, join_url, start_url"]
    G --> I["Notification Sent<br/>to Patient"]
    H --> J["GET /doctor/patients/{patient_id}/documents<br/>Requires Permission"]
    I --> J
    J --> K{Has Permission?}
    K -->|Yes| L["200 OK<br/>Return Documents<br/>Presigned URLs"]
    K -->|No| M["403 Forbidden<br/>Access Denied"]
    L --> N["POST /doctor/tasks<br/>Create Task"]
    M --> N
    N --> O["GET /doctor/tasks<br/>View Tasks"]
    O --> P["PATCH /doctor/tasks/{id}<br/>Update Status"]
    P --> Q["DELETE /doctor/tasks/{id}<br/>Remove Task"]
    Q --> R["POST /auth/logout<br/>End Session"]
    R --> S([Doctor Ends])

    style B fill:#90EE90
    style C fill:#90EE90
    style F fill:#98FB98
    style G fill:#FFB6C1
    style L fill:#87CEEB
    style M fill:#FF6B6B
    style N fill:#FFD700
```

### Doctor API Endpoint Sequence

1. **Register as Doctor**

   ```
   POST /api/v1/auth/register
   Role: doctor
   Fields: specialty, license_number, qualifications
   ```

2. **Login**

   ```
   POST /api/v1/auth/login
   Returns: access_token, refresh_token, user_info
   ```

3. **View Pending Appointments**

   ```
   GET /api/v1/appointments
   Returns: List of appointment requests
   Status: PENDING (waiting for doctor decision)
   ```

4. **Approve Appointment (Creates Zoom)**

   ```
   POST /api/v1/appointments/{appointment_id}/approve
   Body:
     - appointment_time: ISO 8601 datetime
     - doctor_notes: Optional notes
   Returns:
     - meeting_id: Zoom meeting ID
     - join_url: Doctor's Zoom join link
     - start_url: Doctor's Zoom start link
     - patient_join_url: Patient's Zoom join link
   Status updated to: APPROVED
   ```

5. **Decline Appointment**

   ```
   PATCH /api/v1/appointments/{appointment_id}/status
   Body:
     - status: DECLINED
     - reason: Optional reason for decline
   Patient notification sent automatically
   Status updated to: DECLINED
   ```

6. **Access Patient Documents**

   ```
   GET /api/v1/doctor/patients/{patient_id}/documents
   Permission check:
     - Does DataAccessGrant exist? OR
     - Does active appointment exist?
   If permitted: Returns list with presigned URLs (15 min expiry)
   If denied: Returns 403 Forbidden
   ```

7. **Create Task**

   ```
   POST /api/v1/doctor/tasks
   Body:
     - title: Task title
     - description: Task details
     - priority: HIGH, MEDIUM, LOW
     - due_date: ISO 8601 datetime
     - patient_id: Optional link to patient
   Returns: task_id, created_at
   ```

8. **View All Tasks**

   ```
   GET /api/v1/doctor/tasks
   Query params:
     - status: PENDING, IN_PROGRESS, COMPLETED
     - priority: HIGH, MEDIUM, LOW
     - patient_id: Optional filter
   Returns: List of tasks
   ```

9. **Update Task**

   ```
   PATCH /api/v1/doctor/tasks/{task_id}
   Body:
     - status: PENDING, IN_PROGRESS, COMPLETED
     - notes: Update notes
     - priority: Updated priority
   Returns: Updated task object
   ```

10. **Delete Task**

    ```
    DELETE /api/v1/doctor/tasks/{task_id}
    Returns: 204 No Content
    ```

11. **Logout**
    ```
    POST /api/v1/auth/logout
    Invalidates refresh_token
    ```

---

## 🤖 AI Document Processing Flow

### Visual Flow Diagram

```mermaid
sequenceDiagram
    participant P as Patient/Doctor
    participant API as API Server
    participant C as Celery Worker
    participant AI as Bedrock/Textract

    P->>API: POST /api/v1/documents/upload
    API-->>P: 201 Created (document_id, status: processing)
    API->>C: Trigger process_document_task

    rect rgb(240, 240, 240)
        Note over C, AI: Background Processing
        C->>AI: Step 1: Text Extraction (OCR)
        AI-->>C: Raw Text
        C->>AI: Step 2: Clinical Entity Extraction
        C->>AI: Step 3: Semantic Vector Indexing
    end

    P->>API: GET /api/v1/documents/{id}/status
    API-->>P: Status: "indexed" (Ready for Analysis)

    P->>API: POST /api/v1/doctor/ai/chat/doctor
    API->>C: RAG Context Retrieval
    C-->>API: LLM Informed Insights
    API-->>P: Streaming SSE Response (Medical Intelligence)
```

---

## 🔄 Complete System Interaction Flow

### Visual System Interaction Diagram

```mermaid
graph TB
    subgraph Patient["👤 PATIENT"]
        P1["Register"] --> P2["Login"]
        P2 --> P3["Upload Documents<br/>5+ files"]
        P3 --> P4["Search Doctors"]
        P4 --> P5["Request Appointment<br/>grant_access=true"]
        P5 --> P6["Check Status"]
        P6 --> P7{Status?}
        P7 -->|PENDING| P6
        P7 -->|APPROVED| P8["Access Zoom Link<br/>Join Meeting"]
        P7 -->|DECLINED| P9["Rejected<br/>Try Another Doctor"]
    end

    subgraph Doctor["👨‍⚕️ DOCTOR"]
        D1["Register<br/>specialty, license"] --> D2["Login"]
        D2 --> D3["View Requests"]
        D3 --> D4{Approve or<br/>Decline?}
        D4 -->|Approve| D5["Create Zoom<br/>meeting_id, join_url"]
        D4 -->|Decline| D6["Send Decline<br/>to Patient"]
        D5 --> D7["View Patient<br/>Documents"]
        D6 --> D7
        D7 --> D8{Check<br/>Permission}
        D8 -->|Yes| D9["Access Granted<br/>Presigned URLs"]
        D8 -->|No| D10["403 Forbidden"]
        D9 --> D11["Create Tasks<br/>for Follow-up"]
        D11 --> D12["Manage Tasks<br/>Update/Delete"]
    end

    subgraph System["🔐 SYSTEM LAYER"]
        S1["Database<br/>PostgreSQL"]
        S2["Document Storage<br/>MinIO + Encryption"]
        S3["Zoom API<br/>Meeting Integration"]
        S4["Authentication<br/>JWT Tokens"]
        S5["Audit Logs<br/>HIPAA Compliance"]
    end

    P5 -.->|Grant Access| D8
    D5 -.->|Zoom Link| P8
    D6 -.->|Notification| P9

    P1 --> S1
    P3 --> S2
    P5 --> S1
    D1 --> S1
    D5 --> S3
    D7 --> S2

    D9 --> S5
    D10 --> S5
    P5 --> S4

    style P5 fill:#FFD700
    style D5 fill:#98FB98
    style D9 fill:#87CEEB
    style D10 fill:#FF6B6B
    style S5 fill:#FFA500
```

### System Interaction Key Points

1. **Patient Grants Access:** `grant_access_to_history: true` in appointment request
2. **Creates DataAccessGrant:** Stored in database for permission checking
3. **Doctor Approval:** Triggers Zoom API to create meeting
4. **Document Access:** Checked before returning presigned URLs
5. **Audit Trail:** All PHI access logged for HIPAA compliance
6. **Notification:** Asynchronous notifications to patient
7. **Encryption:** Documents encrypted at rest in MinIO storage

---

## 🔐 Permission-Based Access Control

### Access Control Flow Diagram

```mermaid
graph LR
    A["Patient Creates<br/>Appointment"] --> B["grant_access_to_history<br/>true"]
    B --> C["DataAccessGrant<br/>Created in DB"]

    D["Doctor Requests<br/>Patient Documents"] --> E{Permission<br/>Check}

    E --> F{DataAccessGrant<br/>Exists?}
    E --> G{Active<br/>Appointment?}

    F -->|Yes| H["✅ Access<br/>Granted"]
    G -->|Yes| H
    F -->|No| I["Check Next"]
    G -->|No| J["❌ Access<br/>Denied<br/>403 Forbidden"]
    I --> J

    H --> K["200 OK<br/>Return Documents<br/>Presigned URLs<br/>15 min expiry"]
    J --> L["Audit Log<br/>Access Denied"]
    K --> M["Audit Log<br/>Access Granted"]

    style A fill:#FFD700
    style H fill:#98FB98
    style J fill:#FF6B6B
    style M fill:#FFA500
    style L fill:#FFA500
```

### Permission Logic in Detail

**When Doctor Requests Patient Documents:**

1. **Check DataAccessGrant Exists**
   - Did patient include `grant_access_to_history: true` in appointment request?
   - Is the grant still active (not expired)?

2. **Check Active Appointment**
   - Is there an appointment between this doctor and patient?
   - Is the appointment status APPROVED or COMPLETED?

3. **Decision Matrix**

   ```
   DataAccessGrant  |  Active Appointment  |  Result
   ─────────────────┼──────────────────────┼──────────────
   Yes              |  Any                 |  ✅ ALLOW
   No               |  Yes                 |  ✅ ALLOW
   No               |  No                  |  ❌ DENY (403)
   ```

4. **If Access Granted**
   - Generate presigned URLs (15 minute expiry)
   - Log access event with doctor_id, patient_id, timestamp
   - Return list of documents with secure URLs

5. **If Access Denied**
   - Return 403 Forbidden
   - Log denied access attempt
   - Do NOT expose patient data in error message

---

## 📋 API Endpoint Categorization

### Authentication Endpoints

```mermaid
graph TD
    Auth["🔐 Authentication<br/>Endpoints"]

    Auth --> A1["POST /auth/register<br/>Register new user"]
    Auth --> A2["POST /auth/login<br/>Get JWT tokens"]
    Auth --> A3["POST /auth/logout<br/>Invalidate tokens"]
    Auth --> A4["POST /auth/refresh<br/>Refresh access token"]
    Auth --> A5["GET /auth/me<br/>Get current user"]
    Auth --> A6["POST /auth/verify-mfa<br/>Verify MFA code"]

    A1 --> DB1["Database"]
    A2 --> DB1
    A4 --> DB1

    style Auth fill:#90EE90
    style A1 fill:#FFEB3B
    style A2 fill:#FFEB3B
    style A3 fill:#FFEB3B
    style A4 fill:#FFEB3B
    style A5 fill:#FFEB3B
```

### Patient Endpoints

```mermaid
graph TD
    Pat["👤 Patient<br/>Endpoints"]

    Pat --> P1["POST /patient/medical-history<br/>Upload documents"]
    Pat --> P2["GET /doctors/search<br/>Find doctors"]
    Pat --> P3["POST /appointments/request<br/>Request appointment"]
    Pat --> P4["GET /appointments<br/>View appointments"]
    Pat --> P5["GET /patient/permissions<br/>View access grants"]
    Pat --> P6["DELETE /patient/permissions/{id}<br/>Revoke access"]
    Pat --> P7["GET /documents/{id}/status<br/>Check AI Status"]

    P1 --> Storage["MinIO Storage<br/>Encrypted"]
    P3 --> DB["PostgreSQL<br/>Database"]
    P4 --> DB
    P5 --> DB

    style Pat fill:#87CEEB
    style P1 fill:#ADD8E6
    style P3 fill:#FFD700
    style P5 fill:#FFA500
```

### Doctor Endpoints

```mermaid
graph TD
    Doc["👨‍⚕️ Doctor<br/>Endpoints"]

    Doc --> D1["GET /appointments<br/>View requests"]
    Doc --> D2["POST /appointments/{id}/approve<br/>Approve appointment"]
    Doc --> D3["PATCH /appointments/{id}/status<br/>Decline appointment"]
    Doc --> D4["GET /doctor/patients/{id}/documents<br/>View patient records"]
    Doc --> D5["POST /doctor/tasks<br/>Create task"]
    Doc --> D6["GET /doctor/tasks<br/>View tasks"]
    Doc --> D7["PATCH /doctor/tasks/{id}<br/>Update task"]
    Doc --> D8["DELETE /doctor/tasks/{id}<br/>Delete task"]
    Doc --> D9["POST /doctor/ai/process-document<br/>Trigger AI Analysis"]
    Doc --> D10["POST /doctor/ai/chat/doctor<br/>Medical Research Chat"]

    D1 --> DB["Database"]
    D2 --> Zoom["Zoom API"]
    D4 --> Storage["MinIO + DB"]

    style Doc fill:#98FB98
    style D2 fill:#FF69B4
    style D4 fill:#87CEEB
    style D5 fill:#FFD700
```

### Full Endpoint Reference Table

| Method | Endpoint                          | Auth           | Role           | Purpose                               |
| ------ | --------------------------------- | -------------- | -------------- | ------------------------------------- |
| POST   | `/auth/register`                  | No             | Any            | Register new account                  |
| POST   | `/auth/login`                     | No             | Any            | Login and get tokens                  |
| POST   | `/auth/logout`                    | Yes            | Any            | Logout and invalidate tokens          |
| POST   | `/auth/verify-mfa`                | No             | Any            | Submit MFA code                       |
| POST   | `/auth/refresh`                   | No             | Any            | Get new access token                  |
| GET    | `/auth/me`                        | Yes            | Any            | Get current user info                 |
| POST   | `/patient/medical-history`        | Patient        | Patient        | Upload medical documents              |
| POST   | `/documents/upload`               | Patient        | Patient        | Direct medical file upload            |
| GET    | `/documents/{id}/status`          | Patient        | Patient        | Check AI indexing status              |
| GET    | `/doctors/search`                 | Patient        | Patient        | Search for doctors                    |
| POST   | `/appointments/request`           | Patient        | Patient        | Request appointment                   |
| GET    | `/appointments`                   | Patient/Doctor | Patient/Doctor | View appointments                     |
| POST   | `/appointments/{id}/approve`      | Doctor         | Doctor         | Approve appointment (create Zoom)     |
| PATCH  | `/appointments/{id}/status`       | Doctor         | Doctor         | Decline appointment                   |
| GET    | `/doctor/patients/{id}/documents` | Doctor         | Doctor         | View patient documents (if permitted) |
| POST   | `/doctor/ai/process-document`     | Doctor         | Doctor         | Trigger AI processing                 |
| POST   | `/doctor/ai/chat/doctor`          | Doctor         | Doctor         | AI Medical Research Chat              |
| GET    | `/patient/permissions`            | Patient        | Patient        | View active access grants             |
| DELETE | `/patient/permissions/{id}`       | Patient        | Patient        | Revoke doctor access                  |
| POST   | `/doctor/tasks`                   | Doctor         | Doctor         | Create task                           |
| GET    | `/doctor/tasks`                   | Doctor         | Doctor         | View tasks                            |
| PATCH  | `/doctor/tasks/{id}`              | Doctor         | Doctor         | Update task                           |
| DELETE | `/doctor/tasks/{id}`              | Doctor         | Doctor         | Delete task                           |

---

## 📝 Common API Flows

### Flow 1: Complete Patient Appointment Booking

**Step 1: Patient Registration**

```http
POST /auth/register
```

```json
{
  "email": "patient@example.com",
  "password": "securePassword123",
  "full_name": "John Doe",
  "phone": "+1234567890",
  "role": "patient"
}

Response 201 Created:
{
  "user_id": "pat_001",
  "email": "patient@example.com",
  "role": "patient",
  "message": "Registration successful"
}
```

**Step 2: Patient Login**

```http
POST /auth/login
```

```json
{
  "email": "patient@example.com",
  "password": "securePassword123"
}

Response 200 OK:
{
  "access_token": "eyJhbGc...",
  "refresh_token": "ref_...",
  "token_type": "Bearer",
  "expires_in": 86400,
  "user": {
    "user_id": "pat_001",
    "email": "patient@example.com",
    "role": "patient"
  }
}
```

**Step 3: Upload Medical Documents**

```http
POST /patient/medical-history
```

```json
{
  "documents": [
    {
      "document_id": "doc_001",
      "filename": "file1.pdf",
      "category": "LAB_REPORT",
      "upload_date": "2026-01-28T10:00:00Z",
      "size_mb": 2.5
    }
  ],
  "total_uploaded": 5,
  "message": "Documents uploaded successfully"
}
```

**Step 4: Search for Doctor**

```http
GET /doctors/search?specialty=Cardiology&city=NewYork
```

```json
{
  "doctors": [
    {
      "doctor_id": "doc_001",
      "full_name": "Dr. Smith",
      "specialty": "Cardiology",
      "hospital": "City Medical Center",
      "rating": 4.8,
      "available_slots": 5
    }
  ],
  "total_results": 3
}
```

**Step 5: Request Appointment**

```http
POST /appointments/request
```

```json
{
  "doctor_id": "doc_001",
  "requested_date": "2026-02-15T10:00:00Z",
  "reason": "Cardiac checkup",
  "description": "Annual checkup and test results review",
  "grant_access_to_history": true
}

Response 201 Created:
{
  "appointment_id": "apt_001",
  "doctor_id": "doc_001",
  "doctor_name": "Dr. Smith",
  "status": "PENDING",
  "requested_date": "2026-02-15T10:00:00Z",
  "created_at": "2026-01-28T10:00:00Z",
  "message": "Appointment request sent. Awaiting doctor approval."
}
```

**Step 6: Check Appointment Status**

```http
GET /appointments
```

```json
{
  "appointments": [
    {
      "appointment_id": "apt_001",
      "doctor_id": "doc_001",
      "doctor_name": "Dr. Smith",
      "status": "PENDING",
      "requested_date": "2026-02-15T10:00:00Z",
      "created_at": "2026-01-28T10:00:00Z"
    }
  ]
}
```

**Step 7: Doctor Approves (Doctor Side)**

```
POST /appointments/{appointment_id}/approve
Authorization: Bearer {doctor_token}
Content-Type: application/json

{
  "appointment_time": "2026-02-15T10:00:00Z",
  "doctor_notes": "Looking forward to the consultation"
}

Response 200 OK:
{
  "appointment_id": "apt_001",
  "status": "APPROVED",
  "zoom_meeting": {
    "meeting_id": "123456789",
    "join_url": "https://zoom.us/j/123456789",
    "start_url": "https://zoom.us/s/123456789",
    "password": "abc123"
  },
  "appointment_time": "2026-02-15T10:00:00Z"
}
```

**Step 8: Patient Joins Meeting**

```
GET /appointments
Authorization: Bearer {patient_token}

Response 200 OK:
{
  "appointments": [
    {
      "appointment_id": "apt_001",
      "doctor_name": "Dr. Smith",
      "status": "APPROVED",
      "appointment_time": "2026-02-15T10:00:00Z",
      "zoom_meeting": {
        "join_url": "https://zoom.us/j/123456789"
      }
    }
  ]
}
```

---

### Flow 2: Doctor Accesses Patient Documents

**Step 1: Doctor Login**

```
POST /auth/login
{
  "email": "doctor@hospital.com",
  "password": "docPassword123"
}

Response 200 OK: (returns access_token)
```

**Step 2: Check Patient Permission**

```
GET /doctor/patients/{patient_id}/documents
Authorization: Bearer {doctor_token}

Response 200 OK (if permission exists):
{
  "patient": {
    "patient_id": "pat_001",
    "name": "John Doe"
  },
  "documents": [
    {
      "document_id": "doc_001",
      "filename": "blood_work.pdf",
      "category": "LAB_REPORT",
      "presigned_url": "https://minio.../blood_work.pdf?token=xyz&expires=900",
      "expires_in_seconds": 900
    }
  ]
}

Response 403 Forbidden (if no permission):
{
  "error": "Forbidden",
  "message": "Patient has not granted access to medical history",
  "doctor_action": "Request patient permission"
}
```

---

### Flow 3: Doctor Creates and Manages Tasks

**Create Task**

```
POST /doctor/tasks
Authorization: Bearer {doctor_token}
Content-Type: application/json

{
  "title": "Review lab results",
  "description": "Patient John Doe - cardiac panel results",
  "priority": "HIGH",
  "due_date": "2026-01-30T17:00:00Z",
  "patient_id": "pat_001"
}

Response 201 Created:
{
  "task_id": "task_001",
  "title": "Review lab results",
  "status": "PENDING",
  "priority": "HIGH",
  "created_at": "2026-01-28T10:00:00Z"
}
```

**View Tasks**

```
GET /doctor/tasks?status=PENDING&priority=HIGH
Authorization: Bearer {doctor_token}

Response 200 OK:
{
  "tasks": [
    {
      "task_id": "task_001",
      "title": "Review lab results",
      "status": "PENDING",
      "priority": "HIGH",
      "due_date": "2026-01-30T17:00:00Z",
      "patient_id": "pat_001"
    }
  ],
  "total": 1
}
```

**Update Task**

```
PATCH /doctor/tasks/{task_id}
Authorization: Bearer {doctor_token}
Content-Type: application/json

{
  "status": "COMPLETED",
  "notes": "Results reviewed. Patient needs follow-up with cardiologist."
}

Response 200 OK:
{
  "task_id": "task_001",
  "status": "COMPLETED",
  "notes": "Results reviewed. Patient needs follow-up with cardiologist.",
  "completed_at": "2026-01-28T15:00:00Z"
}
```

**Delete Task**

```
DELETE /doctor/tasks/{task_id}
Authorization: Bearer {doctor_token}

Response 204 No Content
```

---

### Flow 4: AI Document Processing & Medical Analysis

**Step 1: Patient Uploads Document**

```
POST /api/v1/documents/upload
Authorization: Bearer {patient_token}
Content-Type: multipart/form-data

Form Data:
- file: [blood_test.pdf]
- notes: "Initial screening"

Response 201 Created:
{
  "success": true,
  "document_id": "7c66994c-0411-44f2-906c-f38cf564d35a",
  "status": "processing"
}
```

**Step 2: Check Processing Status**

```
GET /api/v1/documents/7c66994c-0411-44f2-906c-f38cf564d35a/status
Authorization: Bearer {patient_token}

Response 200 OK:
{
  "id": "7c66994c-0411-44f2-906c-f38cf564d35a",
  "status": "indexed",
  "ai_ready": true
}
```

**Step 3: Doctor Triggers AI Insights**

```
POST /api/v1/doctor/ai/process-document
Authorization: Bearer {doctor_token}
Content-Type: application/json

{
  "patient_id": "pat_001",
  "document_id": "7c66994c-0411-44f2-906c-f38cf564d35a"
}

Response 201 Created:
{
  "message": "AI Analysis triggered",
  "task_id": "task_ai_999"
}
```

**Step 4: AI Research Chat (Streaming)**

```
POST /api/v1/doctor/ai/chat/doctor
Authorization: Bearer {doctor_token}
Content-Type: application/json

{
  "patient_id": "pat_001",
  "document_id": "7c66994c-0411-44f2-906c-f38cf564d35a",
  "query": "Does this report indicate any risk of anemia?"
}

Response: 200 OK (Streaming Response - text/event-stream)
Content: "Based on the hemoglobin levels (10.5 g/dL)..."
```

---

### Flow 5: Secure MFA Verification

**Step 1: Initial Login Request**

```
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "doctor@hospital.com",
  "password": "docPassword123"
}

Response 200 OK (Challenge):
{
  "mfa_required": true,
  "user_id": "doc_888",
  "message": "MFA verification required"
}
```

**Step 2: Submit Verification Code**

```
POST /api/v1/auth/verify-mfa
Content-Type: application/json

{
  "user_id": "doc_888",
  "code": "123456"
}

Response 200 OK:
{
  "access_token": "eyJhbGc...",
  "token_type": "Bearer",
  "user": {
    "id": "doc_888",
    "role": "doctor"
  }
}
```

---

## 🔐 Authentication Flow

### JWT Token Structure

**Access Token (24 hours validity)**

```
Header:
{
  "alg": "HS256",
  "typ": "JWT"
}

Payload:
{
  "user_id": "pat_001",
  "email": "patient@example.com",
  "role": "patient",
  "iat": 1706422800,
  "exp": 1706509200,
  "iss": "saramedico"
}

Signature: HMACSHA256(...)
```

**Refresh Token (30 days validity)**

```
Header:
{
  "alg": "HS256",
  "typ": "JWT"
}

Payload:
{
  "user_id": "pat_001",
  "token_type": "refresh",
  "iat": 1706422800,
  "exp": 1709014800,
  "iss": "saramedico"
}
```

### Token Usage in Requests

**Include in Authorization Header**

```
GET /appointments
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoicGF0XzAwMSIsImVtYWlsIjoicGF0aWVudEBleGFtcGxlLmNvbSIsInJvbGUiOiJwYXRpZW50IiwiaWF0IjoxNzA2NDIyODAwLCJleHAiOjE3MDY1MDkyMDAsImlzcyI6InNhcmFtZWRpY28ifQ.signature
```

### Token Refresh Flow

**When Access Token Expires**

```
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "ref_eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}

Response 200 OK:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 86400
}
```

---

## ✅ Response Status Codes Reference

### 2xx Success Codes

| Code | Status     | When Used                              |
| ---- | ---------- | -------------------------------------- |
| 200  | OK         | Successful GET, PATCH requests         |
| 201  | Created    | Successful POST (new resource created) |
| 204  | No Content | Successful DELETE                      |

### 4xx Client Error Codes

| Code | Status       | When Used                  | Example                                     |
| ---- | ------------ | -------------------------- | ------------------------------------------- |
| 400  | Bad Request  | Invalid request data       | Missing required fields, invalid format     |
| 401  | Unauthorized | Missing or invalid token   | Expired token, no Authorization header      |
| 403  | Forbidden    | No permission for resource | Doctor accessing without patient permission |
| 404  | Not Found    | Resource doesn't exist     | Requesting non-existent appointment         |

### 5xx Server Error Codes

| Code | Status                | When Used               |
| ---- | --------------------- | ----------------------- |
| 500  | Internal Server Error | Unexpected server error |
| 502  | Bad Gateway           | API unavailable         |
| 503  | Service Unavailable   | Server maintenance      |

### Response Format Examples

**Success Response (200 OK)**

```json
{
  "success": true,
  "data": {
    "appointment_id": "apt_001",
    "status": "APPROVED",
    "zoom_meeting": {
      "join_url": "https://zoom.us/j/123456789"
    }
  },
  "message": "Appointment approved successfully"
}
```

**Error Response (403 Forbidden)**

```json
{
  "success": false,
  "error": "Forbidden",
  "message": "Patient has not granted access to medical history",
  "error_code": "NO_PERMISSION",
  "timestamp": "2026-01-28T10:00:00Z"
}
```

**Validation Error (400 Bad Request)**

```json
{
  "success": false,
  "error": "Validation Error",
  "details": [
    {
      "field": "email",
      "message": "Invalid email format"
    },
    {
      "field": "password",
      "message": "Password must be at least 8 characters"
    }
  ],
  "timestamp": "2026-01-28T10:00:00Z"
}
```

---

## 🔒 HIPAA Compliance Details

### 1. Presigned URLs for Document Access

**Security Implementation:**

- Documents never served directly by API
- MinIO generates temporary access URLs
- URLs expire after 15 minutes
- Cannot be reused after expiry
- Each URL tied to specific document
- Access logged automatically

**Example Presigned URL:**

```
https://minio.saramedico.io/medical-documents/
  patient_001/doc_12345.pdf?
  X-Amz-Algorithm=AWS4-HMAC-SHA256&
  X-Amz-Credential=minioadmin/20260128/us-east-1/s3/aws4_request&
  X-Amz-Date=20260128T100000Z&
  X-Amz-Expires=900&
  X-Amz-SignedHeaders=host&
  X-Amz-Signature=xxxxx
```

### 2. Permission-Based Access Control

**Multi-Layer Permission Check:**

1. Authentication: Is user logged in?
2. Authorization: Does user have right role?
3. Permission: Does user have explicit permission?
4. Audit: Log all access attempts

**Permission Scenarios:**

- DataAccessGrant created when patient says "grant_access_to_history: true"
- Only granted permission + active appointment = access
- Expires after appointment or grant expiration
- Can be revoked immediately

### 3. Encryption Standards

**At Rest (Data Storage)**

```
Algorithm: AES-256
Implementation: MinIO encryption
Database: Encrypted columns for PHI
Certificates: TLS 1.2+
```

**In Transit (API Communication)**

```
Protocol: HTTPS/TLS 1.3
All API calls require HTTPS
No plain HTTP connections allowed
Certificate validation enforced
```

### 4. Audit Logging

**What Gets Logged**

- Authentication events (login, logout)
- Document access attempts (success/denied)
- Permission grants and revocations
- All PHI access with doctor_id, patient_id, timestamp
- Failed access attempts with reason

**Log Storage**

- Immutable append-only logs
- Searchable by patient, doctor, date
- Retained for 7 years (regulatory requirement)
- Cannot be deleted by anyone except admin
- Automatically generated for compliance audits

**Audit Log Example**

```
{
  "timestamp": "2026-01-28T10:00:00Z",
  "event_type": "DOCUMENT_ACCESS",
  "doctor_id": "doc_001",
  "patient_id": "pat_001",
  "document_id": "doc_12345",
  "action": "VIEW",
  "result": "SUCCESS",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0..."
}
```

### 5. Data Minimization

**What's NOT Logged**

- Patient passwords
- Credit card numbers
- Social security numbers
- Document content (only metadata)

**What IS Logged**

- Who accessed what document
- When they accessed it
- Whether they were granted permission
- Timestamps for every access

### 6. Patient Rights

**Patient Can:**

- View all doctors with access to their records
- See audit log of who accessed their data
- Revoke access immediately
- Request data deletion
- Download their complete medical history
- Request compliance report

**Patient Cannot:**

- See what doctors did after accessing (privacy)
- Delete audit logs (regulatory requirement)
- Modify doctor notes

---

## 🔗 API Integration Notes

### CORS Configuration

```
Allowed Origins:
  - http://localhost:3000 (development)
  - https://saramedico.com (production)
  - https://app.saramedico.com (production app)

Allowed Methods:
  - GET, POST, PATCH, DELETE, OPTIONS

Allowed Headers:
  - Content-Type
  - Authorization
  - X-Requested-With

Credentials: Include (for cookies)
```

### Rate Limiting

```
Authentication Endpoints: 5 requests/minute per IP
Document Upload: 10 requests/minute per user
Search Endpoints: 30 requests/minute per user
All Others: 60 requests/minute per user

Rate limit headers in response:
  X-RateLimit-Limit: 60
  X-RateLimit-Remaining: 45
  X-RateLimit-Reset: 1706509200
```

### Pagination

```
GET /appointments?page=1&limit=10

Response:
{
  "data": [...],
  "pagination": {
    "current_page": 1,
    "total_pages": 5,
    "total_items": 45,
    "items_per_page": 10,
    "has_next": true,
    "has_previous": false
  }
}
```

---

## 📞 Troubleshooting Guide

### Common Issues and Solutions

**Issue: 401 Unauthorized**

```
Cause: Missing or invalid token
Solution:
  1. Check Authorization header format
  2. Verify token hasn't expired
  3. Use /auth/refresh to get new access_token
```

**Issue: 403 Forbidden on Document Access**

```
Cause: Doctor lacks patient permission
Solution:
  1. Patient must include grant_access_to_history: true
  2. Doctor must wait for appointment approval
  3. Check if grant/appointment has expired
```

**Issue: Document Upload Fails**

```
Cause: File format not supported or size too large
Solution:
  1. Check file is PDF, JPG, or PNG
  2. Verify file size < 100MB
  3. Ensure proper multipart/form-data format
```

**Issue: Zoom Link Invalid**

```
Cause: Doctor hasn't approved appointment yet
Solution:
  1. Wait for doctor approval
  2. Check appointment status is APPROVED
  3. Use join_url from approval response
```

---

## ✨ Best Practices for API Usage

1. **Always Include Authorization Header**

   ```
   Authorization: Bearer {access_token}
   ```

2. **Handle Token Expiry**

   ```
   Check 401 response → Use refresh_token → Retry request
   ```

3. **Use Presigned URLs Immediately**

   ```
   URLs expire after 15 minutes → Download immediately
   ```

4. **Check Permission Before Access**

   ```
   Verify response is not 403 before proceeding
   ```

5. **Log All Important Actions**

   ```
   Appointment requests, document uploads, permission grants
   ```

6. **Implement Proper Error Handling**
   ```
   Catch and display user-friendly error messages
   ```

---

**Document Version:** 2.0  
**Last Updated:** January 2026  
**Status:** Production Ready  
**HIPAA Compliant:** ✅ Yes  
**Ready for Frontend Integration:** ✅ Yes
