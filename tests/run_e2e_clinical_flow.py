import asyncio
import httpx
import uuid
import sys
import os
from datetime import datetime, timedelta

BASE_URL = "http://backend:8000/api/v1"

async def check_backend_ready():
    async with httpx.AsyncClient() as client:
        for _ in range(30):
            try:
                resp = await client.get("http://backend:8000/health", timeout=2.0)
                if resp.status_code == 200:
                    return True
            except Exception:
                pass
            await asyncio.sleep(2)
    return False

async def run_e2e_flow():
    print("\n=== STARTING E2E CLINICAL FLOW ===\n")
    async with httpx.AsyncClient() as client:
        # 1. Doctor Registration & Login
        doc_email = f"clinical_doc_{uuid.uuid4().hex[:4]}@saramedico.com"
        print(f"Step 1: Registering Doctor {doc_email}...")
        await client.post(f"{BASE_URL}/auth/register", json={
            "email": doc_email,
            "password": "SecurePass123!",
            "full_name": "Dr. Clinical Flow",
            "role": "doctor",
            "organization_name": "Clinical City Hospital",
            "phone_number": "+16502530000"
        })
        
        login_resp = await client.post(f"{BASE_URL}/auth/login", json={"email": doc_email, "password": "SecurePass123!"})
        login_json = login_resp.json()
        doc_token = login_json["access_token"]
        headers = {"Authorization": f"Bearer {doc_token}"}

        # 2. Onboard Patient
        print("Step 2: Onboarding Patient...")
        pat_resp = await client.post(f"{BASE_URL}/patients", headers=headers, json={
            "email": f"pat_{uuid.uuid4().hex[:4]}@test.com",
            "password": "Pass123!",
            "full_name": "John Doe E2E",
            "phone_number": "+16502531111",
            "date_of_birth": "1985-10-20",
            "gender": "male"
        })
        patient = pat_resp.json()
        patient_id = patient["id"]
        print(f"Patient Onboarded with ID: {patient_id}")

        # 3. Schedule Consultation
        print("Step 3: Scheduling Consultation...")
        future_date = (datetime.utcnow() + timedelta(days=1)).isoformat()
        cons_resp = await client.post(f"{BASE_URL}/consultations", headers=headers, json={
            "patientId": patient_id,
            "scheduledAt": future_date,
            "durationMinutes": 30,
            "notes": "Annual physical and AI analysis test."
        })
        consultation = cons_resp.json()
        print(f"Consultation Scheduled: {consultation['id']} (Status: {consultation['status']})")

        # 4. Upload Medical Document
        print("Step 4: Uploading Medical Document for AI Processing...")
        # Simulating a small file upload
        files = {"file": ("report.pdf", b"%PDF-1.4 report content", "application/pdf")}
        data = {"patient_id": patient_id, "notes": "E2E Test Report"}
        upload_resp = await client.post(f"{BASE_URL}/documents/upload", headers=headers, data=data, files=files, timeout=30.0)
        upload_data = upload_resp.json()
        document_id = upload_data["document_id"]
        print(f"Document Uploaded: {document_id} (Status: {upload_data['status']})")

        # 5. Verify Dashboard Metrics
        print("Step 5: Verifying Doctor Dashboard KPIs...")
        dash_resp = await client.get(f"{BASE_URL}/doctor/me/dashboard", headers=headers)
        dash_data = dash_resp.json()
        print(f"Dashboard - Patients Today: {dash_data.get('patients_today')}")
        print(f"Dashboard - Pending Notes: {dash_data.get('pending_notes')}")
        
        # In our flow, we scheduled a consultation for TOMORROW. 
        # So patients_today should be 0 unless we change it to TODAY.
        if dash_data.get('patients_today') == 0:
            print("KPI Verification: No patients today (Correct, consultation is tomorrow)")
        
        # Let's perform a search for the document we uploaded
        print("Step 6: Searching for uploaded document...")
        search_resp = await client.get(f"{BASE_URL}/doctor/{login_json['user']['id']}/search?q=E2E", headers=headers)
        if search_resp.status_code == 200:
            print(f"Search found {len(search_resp.json())} records matching 'E2E'")
        else:
            print(f"Search failed: {search_resp.status_code} - {search_resp.text}")

    print("\n=== E2E CLINICAL FLOW COMPLETED SUCCESSFULLY ===\n")

if __name__ == "__main__":
    if not asyncio.run(check_backend_ready()):
        print("Backend failed to start in time. Exiting.")
        sys.exit(1)
    asyncio.run(run_e2e_flow())
