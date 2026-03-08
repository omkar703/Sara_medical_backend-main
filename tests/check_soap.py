import asyncio
import httpx
import uuid
import sys
import time
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
    print("\n=== STARTING SOAP GENERATION TEST ===\n")
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Doctor Registration & Login
        doc_email = f"soap_doc_{uuid.uuid4().hex[:4]}@saramedico.com"
        print(f"[*] Registering Doctor {doc_email}...")
        await client.post(f"{BASE_URL}/auth/register", json={
            "email": doc_email,
            "password": "SecurePass123!",
            "full_name": "Dr. Soap Tester",
            "role": "doctor",
            "organization_name": "Soap Hospital",
            "phone_number": "+16502530000"
        })
        
        login_resp = await client.post(f"{BASE_URL}/auth/login", json={"email": doc_email, "password": "SecurePass123!"})
        login_json = login_resp.json()
        doc_token = login_json.get("access_token")
        if not doc_token:
            print(f"Failed to login doctor: {login_resp.text}")
            sys.exit(1)
        headers = {"Authorization": f"Bearer {doc_token}"}

        # 2. Onboard Patient
        print("[*] Onboarding Patient...")
        pat_resp = await client.post(f"{BASE_URL}/patients", headers=headers, json={
            "email": f"soap_pat_{uuid.uuid4().hex[:4]}@test.com",
            "password": "Pass123!",
            "full_name": "John Doe Soap",
            "phone_number": "+16502531111",
            "date_of_birth": "1985-10-20",
            "gender": "male"
        })
        if pat_resp.status_code != 201:
            print(f"Failed to onboard patient: {pat_resp.text}")
            sys.exit(1)
            
        patient_id = pat_resp.json()["id"]
        print(f"[*] Patient Onboarded with ID: {patient_id}")

        # 3. Schedule Consultation
        print("[*] Scheduling Consultation...")
        now_date = (datetime.utcnow() + timedelta(days=1)).isoformat()
        cons_resp = await client.post(f"{BASE_URL}/consultations", headers=headers, json={
            "patientId": patient_id,
            "scheduledAt": now_date,
            "durationMinutes": 30,
            "notes": "Testing SOAP generation."
        })
        if cons_resp.status_code != 200:
             print(f"Failed to schedule consultation: {cons_resp.text}")
             sys.exit(1)
             
        consultation_id = cons_resp.json()["id"]
        print(f"[*] Consultation Scheduled: {consultation_id}")

        # 4. Insert mock transcript via DB
        print("[*] Simulating Google Meet transcript insertion...")
        import asyncpg
        conn = await asyncpg.connect("postgresql://saramedico_user:SaraMed1c0_Dev_2024!Secure@postgres:5432/saramedico_dev")
        mock_transcript = "Dr. Soap: Are you having chest pain?\nPatient: Yes, it started yesterday."
        await conn.execute("UPDATE consultations SET transcript = $1 WHERE id = $2::UUID", mock_transcript, consultation_id)
        await conn.close()

        # 5. Mark Consultation as Completed
        print("[*] Marking consultation as completed to trigger Celery SOAP task...")
        comp_resp = await client.put(f"{BASE_URL}/consultations/{consultation_id}", headers=headers, json={"status": "completed"})
        if comp_resp.status_code != 200:
            print(f"Failed to complete consultation: {comp_resp.text}")
            sys.exit(1)
        
        print("[*] Consultation completed. Waiting for Celery SOAP Note Generation...")
        
        # 5. Poll for SOAP note
        success = False
        for i in range(12): # Poll for up to 60 seconds
            await asyncio.sleep(5)
            print(f"[*] Polling SOAP note... (Attempt {i+1})")
            soap_resp = await client.get(f"{BASE_URL}/consultations/{consultation_id}/soap-note", headers=headers)
            if soap_resp.status_code == 200:
                soap_data = soap_resp.json()
                print("\n✅ SOAP Note Generated successfully:\n")
                import json
                print(json.dumps(soap_data.get("soap_note"), indent=2))
                success = True
                break
            else:
                print(f"   Status Info: {soap_resp.status_code} - {soap_resp.json()}")
                
        if not success:
            print("\n❌ SOAP Note failed to generate within the timeout.")
            sys.exit(1)

if __name__ == "__main__":
    if not asyncio.run(check_backend_ready()):
        print("Backend failed to start in time. Exiting.")
        sys.exit(1)
    asyncio.run(run_e2e_flow())
