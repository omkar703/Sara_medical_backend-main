# 📊 SaraMedico API Flow Documentation

**Complete API flow diagrams and testing guide are available in the following files:**

## 📁 Documentation Files

1. **[API_FLOW_DIAGRAMS.md](./API_FLOW_DIAGRAMS.md)** ⭐ **START HERE**
   - Comprehensive Mermaid flowcharts
   - Patient journey with all APIs
   - Doctor journey with all APIs
   - System interaction flows
   - Permission-based access control diagrams
   - API endpoint categorization

2. **[flow.md](./flow.md)**
   - Complete test credentials (5 users)
   - All API endpoint examples
   - Request/response samples
   - Manual testing guide
   - Test data (8 documents, 2 appointments)

3. **[COMPLETE_TEST_RESULTS.md](./COMPLETE_TEST_RESULTS.md)**
   - E2E test results (100% pass)
   - All issues resolved
   - Feature verification matrix

4. **[test_complete_flow.py](./test_complete_flow.py)**
   - Automated E2E test script
   - Re-run anytime to test all features

---

## 🚀 Quick Start

### For Visual Learners:

👉 **Open [API_FLOW_DIAGRAMS.md](./API_FLOW_DIAGRAMS.md)**

The file contains:

- 5 comprehensive Mermaid flowcharts
- Patient step-by-step API journey
- Doctor step-by-step API journey
- Complete system interaction map
- Permission flow diagram
- API endpoint categorization

### For Manual Testing:

👉 **Open [flow.md](./flow.md)**

Contains all test credentials:

```
Patients:
  - patient1_@test.com / SecurePass123!
  - patient2_@test.com / SecurePass123!

Doctors:
  - doctor1_@test.com / SecurePass123! (Cardiology)
  - doctor2_@test.com / SecurePass123! (Dermatology)
  - doctor3_@test.com / SecurePass123! (Pediatrics)
```

### For Automated Testing:

```bash
python3 backend/test_complete_flow.py
```

---

## 📊 What's in API_FLOW_DIAGRAMS.md

### 1. Patient Journey Flow

Shows complete patient flow from registration to Zoom meeting:

- Register → Login → Search Doctor → Upload Documents
- Request Appointment → Check Status → Join Zoom Meeting

### 2. Doctor Journey Flow

Shows complete doctor workflow:

- Register → Login → View Appointments
- Approve (creates Zoom) OR Decline
- View Patient Records (permission-based)
- Manage Tasks (CRUD operations)

### 3. Complete System Interaction

Full end-to-end view showing how patient and doctor sides connect:

- Permission granting
- Zoom link delivery
- Access control enforcement

### 4. Permission-Based Access Control

Detailed diagram of HIPAA-compliant permission system:

- How patients grant access
- How doctors request access
- 200 OK vs 403 Forbidden logic

### 5. API Endpoint Categorization

Visual map of all endpoints organized by category:

- Authentication APIs
- Patient APIs
- Doctor APIs
- Shared resources (Database, MinIO, Zoom)

---

## 🎯 API Flow Summary

### Patient APIs (Sequential Flow):

```
1. POST /auth/register (role: patient)
2. POST /auth/login (get JWT token)
3. GET /doctors/search?specialty=Cardiology
4. POST /patient/medical-history (upload 5+ documents)
5. POST /appointments/request (grant_access_to_history: true)
6. GET /appointments (check status)
7. Use join_url to join Zoom meeting
8. POST /auth/logout
```

### Doctor APIs (Sequential Flow):

```
1. POST /auth/register (role: doctor, specialty, license)
2. POST /auth/login (get JWT token)
3. GET /appointments (view pending requests)
4. POST /appointments/{id}/approve (creates Zoom meeting)
   OR
   PATCH /appointments/{id}/status (decline appointment)
5. GET /doctor/patients/{patient_id}/documents (view records)
6. POST /doctor/tasks (create to-do item)
7. GET /doctor/tasks (list tasks)
8. PATCH /doctor/tasks/{id} (update task)
9. DELETE /doctor/tasks/{id} (delete task)
10. POST /auth/logout
```

---

## 🔐 Permission System

**How it works:**

1. Patient requests appointment with `grant_access_to_history: true`
2. System creates `DataAccessGrant` in database
3. Doctor can now access patient's medical records
4. Without permission: **403 Forbidden**
5. With permission: **200 OK** + presigned URLs

---

## ✅ All Features Tested

- [x] Patient registration & login
- [x] Doctor registration & login
- [x] Medical document upload (8 documents)
- [x] Doctor search (by specialty)
- [x] Appointment request (2 appointments)
- [x] Appointment approval (with Zoom)
- [x] Appointment rejection (without Zoom)
- [x] Authorized access (200 OK)
- [x] Unauthorized access (403 Forbidden)
- [x] Task CRUD operations
- [x] Logout functionality

**Success Rate: 100%** 🎯

---

## 📞 Need Help?

- **Visual flows:** See [API_FLOW_DIAGRAMS.md](./API_FLOW_DIAGRAMS.md)
- **Test credentials:** See [flow.md](./flow.md)
- **Test results:** See [COMPLETE_TEST_RESULTS.md](./COMPLETE_TEST_RESULTS.md)
- **Run tests:** `python3 backend/test_complete_flow.py`

---

**All diagrams are in Mermaid format and can be viewed in:**

- GitHub (renders automatically)
- VS Code (with Mermaid extension)
- Online Mermaid editors
- Markdown preview tools

Enjoy testing! 🚀
