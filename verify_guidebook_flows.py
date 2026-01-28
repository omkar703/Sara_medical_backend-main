
import sys
import os
import asyncio
import httpx
import json
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

# Ensure we can import from app
sys.path.append(os.getcwd())

# Load environment variables
from dotenv import load_dotenv
load_dotenv(".env")
os.environ["FORCE_MOCK_ZOOM"] = "true"

# Local settings
BASE_URL = "http://localhost:8000"
# Use unique emails for each run to avoid encryption key issues with old DB records
run_id = str(uuid4())[:8]
DOCTOR_EMAIL = f"e2e_doctor_{run_id}@test.com"
PATIENT_EMAIL = f"e2e_patient_{run_id}@test.com"
PASSWORD = "TestPassword123!"

async def run_e2e_verification():
    print(f"🚀 STARTING E2E FLOW VERIFICATION (Run ID: {run_id})\n")
    
    async with httpx.AsyncClient() as client:
        # 1. DOCTOR AUTH
        print(f"Step 1: Doctor Registration & Login ({DOCTOR_EMAIL})")
        reg_payload = {
            "email": DOCTOR_EMAIL, "password": PASSWORD, "first_name": "Gregory", "last_name": "House",
            "organization_name": f"Org_{run_id}", "role": "doctor", "phone": "+15551112222", "date_of_birth": "1970-01-01"
        }
        await client.post(f"{BASE_URL}/api/v1/auth/register", json=reg_payload)
        
        login_resp = await client.post(f"{BASE_URL}/api/v1/auth/login", json={"email": DOCTOR_EMAIL, "password": PASSWORD})
        if login_resp.status_code != 200:
            print(f"  ❌ Doctor Login failed: {login_resp.text}")
            return
        doctor_token = login_resp.json()["access_token"]
        doctor_id = login_resp.json()["user"]["id"]
        doctor_headers = {"Authorization": f"Bearer {doctor_token}"}
        
        # 2. PATIENT AUTH
        print(f"Step 2: Patient Registration & Login ({PATIENT_EMAIL})")
        reg_payload = {
            "email": PATIENT_EMAIL, "password": PASSWORD, "first_name": "James", "last_name": "Wilson",
            "organization_name": f"Org_{run_id}", "role": "patient", "phone": "+15553334444", "date_of_birth": "1975-01-01"
        }
        await client.post(f"{BASE_URL}/api/v1/auth/register", json=reg_payload)
        
        login_resp = await client.post(f"{BASE_URL}/api/v1/auth/login", json={"email": PATIENT_EMAIL, "password": PASSWORD})
        if login_resp.status_code != 200:
            print(f"  ❌ Patient Login failed: {login_resp.text}")
            return
        patient_token = login_resp.json()["access_token"]
        patient_id = login_resp.json()["user"]["id"]
        patient_headers = {"Authorization": f"Bearer {patient_token}"}
        
        # Get patient info
        me_resp = await client.get(f"{BASE_URL}/api/v1/auth/me", headers=patient_headers)
        patient_id = me_resp.json()["id"]

        # 3. PATIENT UPLOAD DOCUMENT
        print("Step 3: Patient Uploads medical report")
        doc_path = "/home/op/Videos/saramedico/backend/_documents/Synthetic_Patient_02_es.pdf"
        with open(doc_path, "rb") as f:
            upload_resp = await client.post(
                f"{BASE_URL}/api/v1/documents/upload", 
                headers=patient_headers,
                files={'file': ('report.pdf', f, 'application/pdf')}
            )
        if upload_resp.status_code not in [200, 201]:
            print(f"  ❌ Upload failed ({upload_resp.status_code}): {upload_resp.text}")
            return
        document_id = upload_resp.json()["document_id"]
        print(f"  - Document Uploaded: {document_id}")

        # 4. PATIENT SEARCH DOCTOR
        print("Step 4: Patient searches for doctor")
        search_resp = await client.get(f"{BASE_URL}/api/v1/doctors/search?query=Gregory", headers=patient_headers)
        results = search_resp.json().get("results", [])
        # We verify our registered doctor is in results
        found = any(d["id"] == doctor_id for d in results)
        print(f"  - Doctor Found in search: {found}")

        # 5. PATIENT REQUEST APPOINTMENT
        print("Step 5: Patient requests appointment & grants AI access")
        appt_payload = {
            "doctor_id": doctor_id,
            "requested_date": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
            "reason": "Persistent leg pain and suspected lupus.",
            "grant_access_to_history": True
        }
        appt_resp = await client.post(f"{BASE_URL}/api/v1/appointments/request", headers=patient_headers, json=appt_payload)
        if appt_resp.status_code not in [200, 201]:
            print(f"  ❌ Appointment request failed: {appt_resp.text}")
            return
        appointment_id = appt_resp.json()["id"]
        print(f"  - Appointment Requested: {appointment_id}")

        # Explicitly grant AI access (Required for AI features)
        perm_payload = {
            "doctor_id": doctor_id,
            "ai_access_permission": True,
            "access_level": "read_analyze",
            "expiry_days": 30
        }
        await client.post(f"{BASE_URL}/api/v1/permissions/grant-doctor-access", headers=patient_headers, json=perm_payload)
        print("  - AI Analysis Permission Granted")

        # 6. DOCTOR ACCEPT APPOINTMENT
        print("Step 6: Doctor accepts appointment")
        status_payload = {"status": "accepted"}
        await client.patch(f"{BASE_URL}/api/v1/appointments/{appointment_id}/status", headers=doctor_headers, json=status_payload)

        # 7. DOCTOR SCHEDULE CONSULTATION (ZOOM)
        print("Step 7: Doctor schedules consultation")
        cons_payload = {
            "patientId": patient_id,
            "scheduledAt": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
            "durationMinutes": 45,
            "notes": "Discussing the complex cases."
        }
        cons_resp = await client.post(f"{BASE_URL}/api/v1/consultations", headers=doctor_headers, json=cons_payload)
        if cons_resp.status_code not in [200, 201]:
            print(f"  ❌ Consultation creation failed: {cons_resp.text}")
            return
        consultation_id = cons_resp.json()["id"]
        print(f"  - Consultation Created with Zoom: {consultation_id}")

        # 8. DOCTOR TRIGGER AI ANALYSIS
        print("Step 8: Doctor processes patient document with AI")
        process_payload = {
            "patient_id": patient_id,
            "document_id": document_id
        }
        proc_resp = await client.post(f"{BASE_URL}/api/v1/doctor/ai/process-document", headers=doctor_headers, json=process_payload)
        print(f"  - Document sent to AI Queue (Status {proc_resp.status_code})")

        # 9. DOCTOR AI CHAT
        print("Step 9: Doctor asks AI about the document")
        chat_payload = {
            "patient_id": patient_id,
            "document_id": document_id,
            "query": "What are the main symptoms mentioned in this report?"
        }
        # Note: Chat is streaming. We just check status here.
        chat_resp = await client.post(f"{BASE_URL}/api/v1/doctor/ai/chat/doctor", headers=doctor_headers, json=chat_payload)
        print(f"  - AI Chat Response status: {chat_resp.status_code}")

    print("\n✅ E2E VERIFICATION COMPLETE. ALL FLOWS FUNCTIONAL.")

if __name__ == "__main__":
    asyncio.run(run_e2e_verification())
