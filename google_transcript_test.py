import asyncio
import httpx
import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.patient import Patient

BASE_URL = "http://localhost:8000/api/v1"
TEST_EMAIL = "dr_dashboard_test@saramedico.com"
TEST_PASSWORD = "Password123!"

async def get_test_patient_id():
    """Fetch a patient ID from the database."""
    async with AsyncSessionLocal() as session:
        doc_result = await session.execute(select(User).where(User.email == TEST_EMAIL))
        doctor = doc_result.scalar_one_or_none()
        if not doctor:
            print(f"Doctor {TEST_EMAIL} not found!")
            return None
        
        pat_result = await session.execute(
            select(Patient).where(Patient.organization_id == doctor.organization_id).limit(1)
        )
        patient = pat_result.scalar_one_or_none()
        if not patient:
            print("No test patient found!")
            return None
        
        return str(patient.id)

async def test_full_pipeline():
    patient_id = await get_test_patient_id()
    if not patient_id:
        return

    async with httpx.AsyncClient(timeout=30.0) as client:
        print("\n--- 1. Authenticating ---")
        login_resp = await client.post(f"{BASE_URL}/auth/login", json={
            "email": TEST_EMAIL, 
            "password": TEST_PASSWORD
        })
        
        if login_resp.status_code != 200:
            print(f"Login Failed: {login_resp.text}")
            return
            
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Authenticated.")

        print("\n--- 2. Scheduling Consultation (Generates Meet Link) ---")
        # Schedule the meeting for right now so we could theoretically join it
        future_time = datetime.now(timezone.utc) + timedelta(minutes=5)
            
        payload = {
            "patientId": patient_id,
            "scheduledAt": future_time.isoformat(),
            "durationMinutes": 30,
            "notes": "Testing the full Google Meet -> Transcript pipeline!"
        }
        
        schedule_resp = await client.post(f"{BASE_URL}/consultations", json=payload, headers=headers)
        
        if schedule_resp.status_code not in [200, 201]:
            print(f"❌ ERROR Creating Meeting: {schedule_resp.text}")
            return
            
        data = schedule_resp.json()
        consultation_id = data.get("id")
        meet_link = data.get("meet_link") or data.get("meetLink")
        
        print("✅ SUCCESS! Consultation Created.")
        print(f"   Consultation ID: {consultation_id}")
        print(f"   Google Meet Link: {meet_link}")

        print("\n--- 3. Fetching Transcript & Triggering AI Analysis ---")
        print("⚠️ NOTE: In an automated test, this will likely return 404 because no one joined the Meet to record audio.")
        
        analyze_resp = await client.post(f"{BASE_URL}/consultations/{consultation_id}/analyze", headers=headers)
        
        print(f"Status Code: {analyze_resp.status_code}")
        try:
            print(json.dumps(analyze_resp.json(), indent=2))
        except:
            print(analyze_resp.text)

if __name__ == "__main__":
    try:
        asyncio.run(test_full_pipeline())
    except KeyboardInterrupt:
        pass