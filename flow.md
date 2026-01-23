# SaraMedico E2E Testing Flow
**Generated on:** 2026-01-23 18:34:03

---

## Test Environment
- **Backend URL:** http://localhost:8000/api/v1
- **Total Users:** 5
- **Total Documents:** 8
- **Total Appointments:** 2

---

## 1. User Credentials

### Patients


**Alice Johnson**
- Email: `patient1_1769153638@test.com`
- Password: `SecurePass123!`
- User ID: `62ccc6b6-d335-422f-b56d-fa8fce2902ad`

**Bob Martinez**
- Email: `patient2_1769153638@test.com`
- Password: `SecurePass123!`
- User ID: `78b5055f-8bd0-4890-ab35-8259d03cad95`

### Doctors

**Dr. Sarah Chen**
- Email: `doctor1_1769153638@test.com`
- Password: `SecurePass123!`
- User ID: `cb1ef614-c42f-4a0c-b449-1ab3e0c052b0`
- Specialty: `Cardiology`

**Dr. Michael Brown**
- Email: `doctor2_1769153638@test.com`
- Password: `SecurePass123!`
- User ID: `4b4eae26-f7a8-4226-b63d-9e9bdbae780b`
- Specialty: `Dermatology`

**Dr. Emily Wang**
- Email: `doctor3_1769153638@test.com`
- Password: `SecurePass123!`
- User ID: `41388be3-6252-45c8-8917-38aae28800a2`
- Specialty: `Pediatrics`


---

## 2. Authentication Testing

### Sign Up (POST /api/v1/auth/register)

**Example Request:**
```json
{
  "email": "newuser@test.com",
  "password": "SecurePass123!",
  "full_name": "New User",
  "role": "patient"
}
```

### Login (POST /api/v1/auth/login)

**Example Request:**
```json
{
  "email": "patient1_1769153638@test.com",
  "password": "SecurePass123!"
}
```

**Expected Response:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "user": {
    "id": "...",
    "email": "...",
    "role": "patient"
  }
}
```

### Logout (POST /api/v1/auth/logout)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "refresh_token": "<refresh_token>"
}
```

---

## 3. Medical History Upload

### Patient Upload (POST /api/v1/patient/medical-history)

**Headers:**
```
Authorization: Bearer <patient_access_token>
```

**Form Data:**
- `file`: Medical document (PDF/Image)
- `category`: LAB_REPORT | IMAGING | PAST_PRESCRIPTION | OTHER
- `title`: Document title
- `description`: Document description

**Uploaded Documents:**


- **Blood Test Results** (LAB_REPORT)
  - Patient: Alice Johnson
  - Document ID: `7eaa728c-a6f3-4057-8cd3-9f30a8b29039`

- **Chest X-Ray** (IMAGING)
  - Patient: Alice Johnson
  - Document ID: `886da5c9-0a0a-41d5-a936-0ed4c2194bc1`

- **Previous Medications** (PAST_PRESCRIPTION)
  - Patient: Alice Johnson
  - Document ID: `ad15b1ab-511c-4968-9881-5b4021cf9669`

- **Diabetes Screening** (LAB_REPORT)
  - Patient: Alice Johnson
  - Document ID: `66155155-99a6-4510-80de-5b879f8c1917`

- **Vaccination Record** (OTHER)
  - Patient: Alice Johnson
  - Document ID: `0ea8595c-8bc9-4942-af60-a2a958030c39`

- **Patient 2 Lab 1** (LAB_REPORT)
  - Patient: Bob Martinez
  - Document ID: `f5479b08-cd1f-4f67-929f-41648d96ebfc`

- **Patient 2 Lab 2** (LAB_REPORT)
  - Patient: Bob Martinez
  - Document ID: `2c118640-8249-4c33-8305-5ab28726ccbb`

- **Patient 2 Lab 3** (LAB_REPORT)
  - Patient: Bob Martinez
  - Document ID: `abe03674-6839-4255-94d2-b38299fde4e0`


---

## 4. Doctor Search

### Search by Specialty (GET /api/v1/doctors/search?specialty=Cardiology)

**Headers:**
```
Authorization: Bearer <patient_access_token>
```

**Example Response:**
```json
[
  {
    "id": "...",
    "full_name": "Dr. Sarah Chen",
    "specialty": "Cardiology",
    "license_number": "LIC-..."
  }
]
```

### Search by Name (GET /api/v1/doctors/search?name=Emily)

---

## 5. Appointment Flow

### Request Appointment (POST /api/v1/appointments/request)

**Headers:**
```
Authorization: Bearer <patient_access_token>
```

**Request:**
```json
{
  "doctor_id": "<doctor_uuid>",
  "requested_date": "2026-01-25T10:00:00",
  "reason": "Medical consultation",
  "grant_access_to_history": true
}
```

### Check Appointment Status (GET /api/v1/appointments)

**Headers:**
```
Authorization: Bearer <patient_access_token>
```

### Created Appointments:


**Appointment ID:** `8ee1dbf0-2b80-48c3-a85d-18ef3fc596bd`
- Patient: Alice Johnson
- Doctor: Dr. Sarah Chen
- Status: **accepted**
- Reason: Cardiac evaluation and follow-up
- Date: 2026-01-25T13:04:01.733709Z
- Zoom URL: https://zoom.us/j/93944123907?pwd=vOKLlBOLcbw7SXQ9SNaQc6eBSI0Ypi.1


**Appointment ID:** `b4706f78-d8a6-48e4-bbb4-14c388993b59`
- Patient: Bob Martinez
- Doctor: Dr. Michael Brown
- Status: **declined**
- Reason: Skin rash consultation
- Date: 2026-01-28T13:04:01.746123Z



---

## 6. Doctor Appointment Management

### View Pending Appointments (GET /api/v1/appointments)

**Headers:**
```
Authorization: Bearer <doctor_access_token>
```

### Approve Appointment (POST /api/v1/appointments/{appointment_id}/approve)

**Headers:**
```
Authorization: Bearer <doctor_access_token>
```

**Response includes Zoom meeting link:**
```json
{
  "id": "...",
  "status": "accepted",
  "meeting_id": "123456789",
  "join_url": "https://zoom.us/j/123456789?pwd=...",
  "start_url": "https://zoom.us/s/123456789?..."
}
```

### Reject Appointment (PATCH /api/v1/appointments/{appointment_id}/status)

**Headers:**
```
Authorization: Bearer <doctor_access_token>
```

**Request:**
```json
{
  "status": "declined"
}
```

---

## 7. Zoom Meeting Integration

### Generated Zoom Meetings:


**Meeting for Appointment:** `8ee1dbf0-2b80-48c3-a85d-18ef3fc596bd`
- Doctor: Dr. Sarah Chen
- Patient: Alice Johnson
- Meeting ID: `93944123907`
- Join URL: https://zoom.us/j/93944123907?pwd=vOKLlBOLcbw7SXQ9SNaQc6eBSI0Ypi.1



---

## 8. Medical Records Access

### Doctor Views Patient Documents (GET /api/v1/doctor/patients/{patient_id}/documents)

**Headers:**
```
Authorization: Bearer <doctor_access_token>
```

**Prerequisites:**
- Patient must have granted access via appointment with `grant_access_to_history: true`

**Test Cases:**

✅ **Authorized Access:**
- Doctor ID: `cb1ef614-c42f-4a0c-b449-1ab3e0c052b0` (Dr. Dr. Sarah Chen)
- Patient ID: `62ccc6b6-d335-422f-b56d-fa8fce2902ad` (Patient 1)
- Expected: 200 OK with document list

❌ **Unauthorized Access:**
- Doctor ID: `41388be3-6252-45c8-8917-38aae28800a2` (Dr. Dr. Emily Wang)
- Patient ID: `62ccc6b6-d335-422f-b56d-fa8fce2902ad` (Patient 1)
- Expected: 403 Forbidden

---

## 9. Task Management (Doctor Dashboard)

### Create Task (POST /api/v1/tasks)

**Headers:**
```
Authorization: Bearer <doctor_access_token>
```

**Request:**
```json
{
  "title": "Review patient lab results",
  "priority": "high",
  "due_date": "2026-01-24T10:00:00"
}
```

### View All Tasks (GET /api/v1/tasks)

**Headers:**
```
Authorization: Bearer <doctor_access_token>
```

### Created Tasks:


- **Review Patient 1 Lab Results**
  - ID: `426b9023-d1df-4888-ad66-0065479ef3ca`
  - Doctor: Dr. Sarah Chen
  - Priority: urgent
  - Status: pending

- **Prepare consultation notes**
  - ID: `4fe09b92-5597-4e7b-a381-d551b4fbed43`
  - Doctor: Dr. Sarah Chen
  - Priority: normal
  - Status: pending


---

## 10. Manual Testing Steps

### Step-by-Step Test Flow:

1. **Authentication Test**
   - Sign up new user → Verify 201 Created
   - Login with credentials → Verify 200 OK + JWT token
   - Access protected endpoint → Verify 401 if not authenticated

2. **Medical History Upload**
   - Login as Patient 1
   - Upload 5 different documents (varying categories)
   - Verify presigned URLs are returned
   - Verify 15-minute expiration on URLs

3. **Doctor Search**
   - Login as Patient 1
   - Search for "Cardiology" → Should find Dr. Sarah Chen
   - Search for "Emily" → Should find Dr. Emily Wang

4. **Appointment Request**
   - Login as Patient 1
   - Request appointment with Dr. Sarah Chen
   - Set `grant_access_to_history: true`
   - Check status → Should be "pending"

5. **Doctor Approval**
   - Login as Dr. Sarah Chen
   - View pending appointments
   - Approve Patient 1's appointment
   - Verify Zoom meeting link is generated
   - Verify status changes to "accepted"

6. **Patient Status Check**
   - Login as Patient 1
   - View appointments → Status should be "accepted"
   - Copy Zoom meeting link

7. **Doctor Rejection Test**
   - Create another appointment (Patient 2 → Dr. Michael Brown)
   - Login as Dr. Michael Brown
   - Reject the appointment
   - Verify status changes to "declined"

8. **Medical Access Check (Authorized)**
   - Login as Dr. Sarah Chen
   - Access Patient 1's documents using: `/doctor/patients/{patient_1_id}/documents`
   - Should return 200 OK with document list

9. **Medical Access Check (Unauthorized)**
   - Login as Dr. Emily Wang (no appointment with Patient 1)
   - Try to access Patient 1's documents
   - Should return 403 Forbidden

10. **Task Management**
    - Login as Dr. Sarah Chen
    - Create 3 tasks with different priorities
    - View all tasks → Should see list
    - Update task status (if endpoint exists)

---

## 11. API Endpoints Summary

| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| POST | `/auth/register` | None | User registration |
| POST | `/auth/login` | None | User login |
| POST | `/auth/logout` | Bearer | User logout |
| GET | `/auth/me` | Bearer | Get current user |
| POST | `/patient/medical-history` | Bearer (Patient) | Upload medical document |
| GET | `/doctors/search` | Bearer | Search doctors |
| POST | `/appointments/request` | Bearer (Patient) | Request appointment |
| GET | `/appointments` | Bearer | List user's appointments |
| POST | `/appointments/{id}/approve` | Bearer (Doctor) | Approve appointment (generates Zoom) |
| PATCH | `/appointments/{id}/status` | Bearer (Doctor) | Update appointment status |
| GET | `/doctor/patients/{patient_id}/documents` | Bearer (Doctor) | View patient records (with permission) |
| POST | `/tasks` | Bearer (Doctor) | Create task |
| GET | `/tasks` | Bearer (Doctor) | List tasks |

---

## 12. Expected Results

✅ **All users can successfully:**
- Register and login
- Logout securely

✅ **Patients can:**
- Upload medical documents (5+ files)
- Search for doctors by specialty/name
- Request appointments
- Grant medical access to doctors
- View their appointment status

✅ **Doctors can:**
- View pending appointment requests
- Approve appointments (generates Zoom link)
- Reject appointments
- View authorized patient medical records
- Get 403 error when accessing unauthorized records
- Create and manage tasks

✅ **System ensures:**
- HIPAA compliance (presigned URLs, permission checks)
- Zoom meeting links generated on approval
- Status updates reflected in real-time
- Proper authorization and authentication

---

## 13. Troubleshooting

### Common Issues:

1. **401 Unauthorized**
   - Ensure Bearer token is included in headers
   - Check token hasn't expired

2. **403 Forbidden (Medical Records)**
   - Patient must grant access via `grant_access_to_history: true`
   - Appointment must exist between doctor and patient

3. **404 Patient Profile Not Found**
   - Patient profile may not be created automatically
   - Check if patient record exists in database

4. **Zoom Meeting Not Generated**
   - Verify Zoom credentials in `.env`
   - Check appointment status is "accepted"

---

## End of Test Flow Document
