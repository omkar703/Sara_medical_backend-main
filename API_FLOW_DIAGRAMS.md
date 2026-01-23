# SaraMedico API Flow Diagrams

This document contains comprehensive Mermaid flowchart diagrams showing all API flows for the SaraMedico platform.

---

## 📊 Complete API Flow Overview

### 1. Patient Journey Flow

```mermaid
flowchart TD
    Start([Patient Start]) --> Register[POST /auth/register<br/>role: patient]
    Register --> Login[POST /auth/login<br/>Get JWT Token]
    Login --> SearchDoc[GET /doctors/search<br/>?specialty=Cardiology]
    SearchDoc --> UploadDocs[POST /patient/medical-history<br/>Upload Medical Documents<br/>Categories: LAB_REPORT, IMAGING, etc.]
    UploadDocs --> RequestAppt[POST /appointments/request<br/>doctor_id, requested_date<br/>grant_access_to_history: true]
    RequestAppt --> CheckStatus[GET /appointments<br/>Check appointment status]
    CheckStatus --> WaitApproval{Appointment<br/>Approved?}
    WaitApproval -->|Yes| GetZoom[Appointment Response<br/>Contains Zoom join_url]
    WaitApproval -->|No| WaitMore[Wait for doctor<br/>decision]
    WaitMore --> CheckStatus
    GetZoom --> JoinMeeting[Join Zoom Meeting<br/>using join_url]
    JoinMeeting --> Logout[POST /auth/logout<br/>End session]
    Logout --> End([Patient End])

    style Register fill:#90EE90
    style Login fill:#90EE90
    style UploadDocs fill:#87CEEB
    style RequestAppt fill:#FFD700
    style GetZoom fill:#98FB98
    style JoinMeeting fill:#FF69B4
```

**Patient API Sequence:**

1. `POST /api/v1/auth/register` - Register as patient
2. `POST /api/v1/auth/login` - Get JWT access token
3. `GET /api/v1/doctors/search?specialty=Cardiology` - Find doctors
4. `POST /api/v1/patient/medical-history` - Upload medical documents (5+)
5. `POST /api/v1/appointments/request` - Request appointment with doctor
6. `GET /api/v1/appointments` - Check appointment status
7. Join Zoom meeting when approved
8. `POST /api/v1/auth/logout` - End session

---

### 2. Doctor Journey Flow

```mermaid
flowchart TD
    Start([Doctor Start]) --> Register[POST /auth/register<br/>role: doctor<br/>specialty, license_number]
    Register --> Login[POST /auth/login<br/>Get JWT Token]
    Login --> ViewAppts[GET /appointments<br/>View pending appointments]
    ViewAppts --> Decision{Approve or<br/>Decline?}

    Decision -->|Approve| Approve[POST /appointments/{id}/approve<br/>appointment_time<br/>Generates Zoom Meeting]
    Decision -->|Decline| Decline[PATCH /appointments/{id}/status<br/>status: declined]

    Approve --> ZoomCreated[Response includes:<br/>meeting_id, join_url, start_url]
    Decline --> NoZoom[No Zoom meeting created]

    ZoomCreated --> ViewRecords[GET /doctor/patients/{patient_id}/documents<br/>Requires permission grant]
    NoZoom --> ViewRecords

    ViewRecords --> CheckPerm{Has<br/>Permission?}
    CheckPerm -->|Yes| GetDocs[200 OK<br/>Retrieve patient documents<br/>with presigned URLs]
    CheckPerm -->|No| Denied[403 Forbidden<br/>Access denied]

    GetDocs --> ManageTasks[Task Management]
    Denied --> ManageTasks

    ManageTasks --> CreateTask[POST /doctor/tasks<br/>Create to-do items]
    CreateTask --> ListTasks[GET /doctor/tasks<br/>View all tasks]
    ListTasks --> UpdateTask[PATCH /doctor/tasks/{id}<br/>Update status, notes]
    UpdateTask --> DeleteTask[DELETE /doctor/tasks/{id}<br/>Remove completed tasks]

    DeleteTask --> Logout[POST /auth/logout<br/>End session]
    Logout --> End([Doctor End])

    style Register fill:#90EE90
    style Login fill:#90EE90
    style Approve fill:#98FB98
    style Decline fill:#FFB6C1
    style GetDocs fill:#87CEEB
    style Denied fill:#FF6B6B
    style CreateTask fill:#FFD700
```

**Doctor API Sequence:**

1. `POST /api/v1/auth/register` - Register as doctor (specialty + license)
2. `POST /api/v1/auth/login` - Get JWT access token
3. `GET /api/v1/appointments` - View pending appointment requests
4. **Approve:** `POST /api/v1/appointments/{id}/approve` - Creates Zoom meeting
5. **Decline:** `PATCH /api/v1/appointments/{id}/status` - Reject appointment
6. `GET /api/v1/doctor/patients/{patient_id}/documents` - View patient records (if permission granted)
7. **Task Management:**
   - `POST /api/v1/doctor/tasks` - Create tasks
   - `GET /api/v1/doctor/tasks` - List tasks
   - `PATCH /api/v1/doctor/tasks/{id}` - Update tasks
   - `DELETE /api/v1/doctor/tasks/{id}` - Delete tasks
8. `POST /api/v1/auth/logout` - End session

---

### 3. Complete System Interaction Flow

```mermaid
flowchart TD
    subgraph Patient["👤 PATIENT SIDE"]
        P1[POST /auth/register] --> P2[POST /auth/login]
        P2 --> P3[POST /patient/medical-history<br/>Upload 5+ documents]
        P3 --> P4[GET /doctors/search<br/>Find specialist]
        P4 --> P5[POST /appointments/request<br/>grant_access_to_history: true]
        P5 --> P6[GET /appointments<br/>Check status]
        P6 --> P7{Status?}
        P7 -->|accepted| P8[Access join_url<br/>Join Zoom meeting]
        P7 -->|declined| P9[Appointment rejected]
        P7 -->|pending| P6
    end

    subgraph Doctor["👨‍⚕️ DOCTOR SIDE"]
        D1[POST /auth/register<br/>specialty, license] --> D2[POST /auth/login]
        D2 --> D3[GET /appointments<br/>View requests]
        D3 --> D4{Decision}
        D4 -->|Approve| D5[POST /appointments/{id}/approve<br/>Creates Zoom meeting]
        D4 -->|Decline| D6[PATCH /appointments/{id}/status<br/>status: declined]
        D5 --> D7[GET /doctor/patients/{id}/documents<br/>View medical records]
        D6 --> D7
        D7 --> D8{Has Permission?}
        D8 -->|Yes| D9[200 OK: Documents + presigned URLs]
        D8 -->|No| D10[403 Forbidden]
        D9 --> D11[POST /doctor/tasks<br/>Create tasks]
        D11 --> D12[GET /doctor/tasks<br/>View tasks]
        D12 --> D13[PATCH /doctor/tasks/{id}<br/>Update]
        D13 --> D14[DELETE /doctor/tasks/{id}<br/>Delete]
    end

    subgraph System["🔄 SYSTEM INTERACTIONS"]
        P5 -.Grant Access.-> D7
        D5 -.Zoom Link.-> P8
        D6 -.Notification.-> P9
    end

    style P1 fill:#90EE90
    style P5 fill:#FFD700
    style P8 fill:#FF69B4
    style D5 fill:#98FB98
    style D6 fill:#FFB6C1
    style D9 fill:#87CEEB
    style D10 fill:#FF6B6B
```

**Key Interactions:**

- Patient grants medical access via `grant_access_to_history: true`
- Doctor approval generates Zoom meeting link
- Doctor can access patient records only with permission
- Unauthorized access returns 403 Forbidden

---

### 4. Permission-Based Access Control Flow

```mermaid
flowchart LR
    subgraph Request["📝 Appointment Request"]
        PR[Patient creates appointment<br/>grant_access_to_history: true]
        PR --> DAG[Creates DataAccessGrant<br/>in database]
    end

    subgraph Access["🔐 Doctor Access Attempt"]
        DR[Doctor requests patient documents<br/>GET /doctor/patients/{id}/documents]
        DR --> Check{Permission Check}
        Check --> Q1{Has DataAccessGrant?}
        Check --> Q2{Has Active Appointment?}
    end

    subgraph Result["✅ Access Decision"]
        Q1 -->|Yes| Allow[200 OK<br/>Return documents<br/>Generate presigned URLs]
        Q2 -->|Yes| Allow
        Q1 -->|No| Q2
        Q2 -->|No| Deny[403 Forbidden<br/>Access denied]
    end

    DAG -.Grants Access.-> Q1

    style PR fill:#FFD700
    style DAG fill:#90EE90
    style Allow fill:#98FB98
    style Deny fill:#FF6B6B
```

**Permission Logic:**

1. Patient grants access during appointment request
2. System creates `DataAccessGrant` record
3. Doctor attempts to access records
4. System checks:
   - Does `DataAccessGrant` exist?
   - Is there an active appointment?
5. If either is true → **200 OK** (Access Granted)
6. If both are false → **403 Forbidden** (Access Denied)

---

### 5. API Endpoint Categorization

```mermaid
graph TB
    subgraph Auth["🔐 Authentication APIs"]
        A1[POST /auth/register]
        A2[POST /auth/login]
        A3[POST /auth/logout]
        A4[GET /auth/me]
    end

    subgraph Patient["👤 Patient APIs"]
        PA1[POST /patient/medical-history]
        PA2[GET /doctors/search]
        PA3[POST /appointments/request]
        PA4[GET /appointments]
    end

    subgraph Doctor["👨‍⚕️ Doctor APIs"]
        DA1[GET /appointments]
        DA2[POST /appointments/{id}/approve]
        DA3[PATCH /appointments/{id}/status]
        DA4[GET /doctor/patients/{id}/documents]
        DA5[POST /doctor/tasks]
        DA6[GET /doctor/tasks]
        DA7[PATCH /doctor/tasks/{id}]
        DA8[DELETE /doctor/tasks/{id}]
    end

    subgraph Shared["🔄 Shared Resources"]
        S1[(Database)]
        S2[(MinIO Storage)]
        S3[Zoom API]
    end

    A1 --> S1
    A2 --> S1
    PA1 --> S1
    PA1 --> S2
    PA3 --> S1
    DA2 --> S1
    DA2 --> S3
    DA4 --> S1
    DA4 --> S2

    style A1 fill:#90EE90
    style A2 fill:#90EE90
    style PA1 fill:#87CEEB
    style PA3 fill:#FFD700
    style DA2 fill:#98FB98
    style DA4 fill:#87CEEB
    style S3 fill:#FF69B4
```

---

## 📝 API Reference Quick Guide

### Authentication Endpoints

| Method | Endpoint         | Auth Required | Description                        |
| ------ | ---------------- | ------------- | ---------------------------------- |
| POST   | `/auth/register` | No            | Register new user (patient/doctor) |
| POST   | `/auth/login`    | No            | Login and get JWT tokens           |
| POST   | `/auth/logout`   | Yes           | Invalidate refresh token           |
| GET    | `/auth/me`       | Yes           | Get current user info              |

### Patient Endpoints

| Method | Endpoint                   | Auth Required | Description                      |
| ------ | -------------------------- | ------------- | -------------------------------- |
| POST   | `/patient/medical-history` | Patient       | Upload medical documents         |
| GET    | `/doctors/search`          | Patient       | Search doctors by specialty/name |
| POST   | `/appointments/request`    | Patient       | Request appointment with doctor  |
| GET    | `/appointments`            | Patient       | List patient's appointments      |

### Doctor Endpoints

| Method | Endpoint                          | Auth Required | Description                         |
| ------ | --------------------------------- | ------------- | ----------------------------------- |
| GET    | `/appointments`                   | Doctor        | View appointment requests           |
| POST   | `/appointments/{id}/approve`      | Doctor        | Approve appointment + create Zoom   |
| PATCH  | `/appointments/{id}/status`       | Doctor        | Update appointment status (decline) |
| GET    | `/doctor/patients/{id}/documents` | Doctor        | View patient medical records \*     |
| POST   | `/doctor/tasks`                   | Doctor        | Create to-do task                   |
| GET    | `/doctor/tasks`                   | Doctor        | List all tasks                      |
| PATCH  | `/doctor/tasks/{id}`              | Doctor        | Update task status/notes            |
| DELETE | `/doctor/tasks/{id}`              | Doctor        | Delete task                         |

\* Requires patient permission (`DataAccessGrant` or active appointment)

---

## ��� Common API Flows

### Flow 1: Patient Books Appointment

```
1. POST /auth/login (patient credentials)
   → Get access_token

2. GET /doctors/search?specialty=Cardiology
   → Find available doctors

3. POST /appointments/request
   Body: {
     "doctor_id": "<doctor_uuid>",
     "requested_date": "2026-01-25T10:00:00",
     "reason": "Cardiac checkup",
     "grant_access_to_history": true
   }
   → Appointment created (status: pending)

4. GET /appointments
   → Check if approved
```

### Flow 2: Doctor Approves with Zoom

```
1. POST /auth/login (doctor credentials)
   → Get access_token

2. GET /appointments
   → View pending requests

3. POST /appointments/{appointment_id}/approve
   Body: {
     "appointment_time": "2026-01-25T10:00:00",
     "doctor_notes": "Looking forward to consultation"
   }
   → Returns: meeting_id, join_url, start_url

4. GET /doctor/patients/{patient_id}/documents
   → Access patient's medical records (5+ documents)
```

### Flow 3: Doctor Manages Tasks

```
1. POST /doctor/tasks
   Body: {
     "title": "Review lab results",
     "description": "Check patient blood work",
     "priority": "urgent",
     "due_date": "2026-01-24T10:00:00"
   }

2. GET /doctor/tasks
   → List all tasks

3. PATCH /doctor/tasks/{task_id}
   Body: {
     "status": "completed",
     "notes": "Results reviewed, all normal"
   }

4. DELETE /doctor/tasks/{task_id}
   → Remove completed task
```

---

## 🔑 Authentication Flow

All protected endpoints require a Bearer token in the Authorization header:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Token Expiry:**

- Access Token: 24 hours (1440 minutes)
- Refresh Token: 30 days

**Refresh Token:**
Use `POST /auth/refresh` with refresh_token to get new access_token

---

## ✅ Response Status Codes

| Code | Meaning      | When It Occurs                                  |
| ---- | ------------ | ----------------------------------------------- |
| 200  | OK           | Successful GET, PATCH                           |
| 201  | Created      | Successful POST (resource created)              |
| 204  | No Content   | Successful DELETE                               |
| 400  | Bad Request  | Invalid request data                            |
| 401  | Unauthorized | Missing or invalid token                        |
| 403  | Forbidden    | No permission (e.g., accessing patient records) |
| 404  | Not Found    | Resource doesn't exist                          |
| 500  | Server Error | Internal server error                           |

---

## 🎯 HIPAA Compliance Notes

1. **Presigned URLs:** All medical documents use 15-minute expiring presigned URLs
2. **Permission Required:** Doctors can only access records with explicit patient consent
3. **Audit Logging:** All access attempts are logged
4. **Encryption:** Medical documents encrypted at rest in MinIO
5. **403 Forbidden:** Returned when doctor lacks permission

---

**For detailed test credentials and example data, see the main flow.md file.**
