# Master API & E2E Testing Prompt for Saramedico Backend

Use this prompt to instruct Antigravity to perform a full system audit, endpoint refinement, and end-to-end flow testing.

---

## **The Task**
Perform a comprehensive, automated, and investigative test of the **Saramedico Backend** project. Your goal is to ensure every API endpoint is fully functional, secure, and integrated correctly into the platform's multi-role workflows.

### **1. Preparation & Environment Audit**
- **Service Check:** Verify that all Docker containers (Postgres, Redis, MinIO, MailHog, Backend, Celery) are healthy.
- **Dependency Mapping:** Analyze `app/main.py` and `app/api/v1/__init__.py` to create a list of all registered endpoints.
- **Database State:** Ensure the database is migrated to the latest version (`alembic upgrade head`) and seed data if necessary for flow testing.

### **2. Security & Compliance Testing**
- **Role-Based Access Control (RBAC):** Test that patients cannot access doctor endpoints, and vice-versa.
- **Multi-Tenancy:** Verify that a doctor from "Hospital A" cannot access data from "Hospital B" (Cross-Hospital Isolation).
- **Audit Logs:** Ensure every sensitive data access (GET patient, GET document) creates a corresponding entry in the `activity_logs` or `audit` tables.
- **Token Rotation:** Test JWT login and refresh token lifecycle.

### **3. Flow-Wise End-to-End (E2E) Testing**
Execute the following primary user journeys and verify every API call in the sequence:

#### **Flow A: The Patient Record Journey**
1.  **Register/Login** as a patient.
2.  **Profile Setup:** Update profile with PII data (Verify encryption in DB).
3.  **Document Management:** Upload a medical PDF -> Check processing status -> Verify it's stored in MinIO.
4.  **AI Interaction:** Query the AI assistant about the uploaded document (Verify RAG/Embeddings logic).

#### **Flow B: The Doctor-Patient Permission Journey**
1.  **Organization Setup:** As an Admin, create a Hospital and invite a Doctor.
2.  **Access Request:** As a Doctor, search for a Patient and request `read_analyze` permission.
3.  **Granting Access:** As a Patient, view pending requests and grant access to the Doctor.
4.  **Clinical Review:** As the Doctor, view the patient's records and use AI to generate a consultation summary.

#### **Flow C: The Virtual Consultation Journey**
1.  **Appointment Booking:** Patient requests an appointment with a specific slot.
2.  **Doctor Confirmation:** Doctor accepts the appointment.
3.  **Sync Verification:** Verify a Calendar Event is created, a Reminder Task is set, and a Zoom/Meet link is generated.
4.  **Post-Consultation:** Doctor records a voice note -> Transcribe to text -> Link to consultation record.

### **4. Endpoint Refinement & Cleanup**
- **Redundancy Check:** Identify any orphaned endpoints or duplicate logic (e.g., `doctor.py` vs `doctors.py`).
- **Response Validation:** Ensure all JSON responses match the Pydantic schemas defined in `/app/schemas`.
- **Error Handling:** Intentionally hit endpoints with missing headers or bad payloads to verify HIPAA-compliant error messages (no leakage of system info).

### **5. Required Deliverable: Comprehensive Testing Report**
Generate a file named `FULL_SYSTEM_TEST_REPORT.md` including:
- **Endpoint Inventory:** A table of all tested endpoints with Method, Path, Auth Level, and Status (Success/Fail).
- **Flow Results:** Detailed logs of the E2E journeys performed.
- **Dependency Matrix:** For each flow, list the sequence of "Pre-requisite APIs" (e.g., *To test 'Analyze Document', you first need 'Auth:Login' -> 'Doc:Upload' -> 'Audit:Status'*).
- **Security Vulnerabilities:** Any discovered gaps in RBAC or tenancy isolation.
- **Refinement Recommendations:** Suggestions for code cleanup or API optimization.

---

**Execution Rule:** Do not just run existing tests. Write new temporary test scripts (`/tmp/verify_xxx.py`) or use `curl` commands to interact with the LIVE dev server to ensure real-world behavior validation.
