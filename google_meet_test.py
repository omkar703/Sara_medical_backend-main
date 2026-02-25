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
    """Fetch a patient ID from the database to use in the API request."""
    async with AsyncSessionLocal() as session:
        # Find our test doctor
        doc_result = await session.execute(select(User).where(User.email == TEST_EMAIL))
        doctor = doc_result.scalar_one_or_none()
        if not doctor:
            print(f"Doctor {TEST_EMAIL} not found! Run the seed script first.")
            return None
        
        # Find any patient in the same organization
        pat_result = await session.execute(
            select(Patient).where(Patient.organization_id == doctor.organization_id).limit(1)
        )
        patient = pat_result.scalar_one_or_none()
        if not patient:
            print("No test patient found in the database!")
            return None
        
        return str(patient.id)

async def test_google_meet_integration():
    patient_id = await get_test_patient_id()
    if not patient_id:
        return

    async with httpx.AsyncClient(timeout=30.0) as client:
        print("\n--- 1. Authenticating as Doctor ---")
        login_resp = await client.post(f"{BASE_URL}/auth/login", json={
            "email": TEST_EMAIL, 
            "password": TEST_PASSWORD
        })
        
        if login_resp.status_code != 200:
            print(f"Login Failed: {login_resp.text}")
            return
            
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("Authenticated successfully.")

        print("\n--- 2. Scheduling Consultation (Triggers Google Meet API) ---")
        # Schedule the meeting 2 hours from now
        future_time = datetime.now(timezone.utc) + timedelta(hours=2)
        
        payload = {
            "patientId": patient_id,
            "scheduledAt": future_time.isoformat(),
            "durationMinutes": 30,
            "notes": "Testing the new Google Meet integration!"
        }
        
        print("Sending Request to /api/v1/consultations...")
        schedule_resp = await client.post(f"{BASE_URL}/consultations", json=payload, headers=headers)
        
        print(f"Status: {schedule_resp.status_code}")
        
        if schedule_resp.status_code in [200, 201]:
            data = schedule_resp.json()
            print("\n✅ SUCCESS! Consultation Created.")
            print(json.dumps(data, indent=2))
            
            # FastAPI might serialize using the alias (google_event_id) or the property name (googleEventId)
            meet_link = data.get("meet_link") or data.get("meetLink")
            
            if meet_link:
                print(f"\n🎉 GOOGLE MEET LINK GENERATED: {meet_link}")
                print("Click the link above to verify it opens a real Google Meet room!")
            else:
                print("\n⚠️ Warning: The consultation was created, but no Meet link was returned.")
        else:
            print(f"\n❌ ERROR: {schedule_resp.text}")

if __name__ == "__main__":
    # Ensure no warnings break the asyncio loop
    try:
        asyncio.run(test_google_meet_integration())
    except KeyboardInterrupt:
        pass