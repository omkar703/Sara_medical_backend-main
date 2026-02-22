import asyncio
import httpx
import json
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.user import User, Organization, Invitation
from app.models.patient import Patient
from app.models.consultation import Consultation
from app.models.task import Task
from app.models.calendar_event import CalendarEvent
from app.core.security import hash_password, pii_encryption

BASE_URL = "http://localhost:8000/api/v1"
TEST_EMAIL = "dr_dashboard_test@saramedico.com"
TEST_PASSWORD = "Password123!"

async def seed_database():
    print("\n--- Seeding Database with Dummy Data ---")
    async with AsyncSessionLocal() as session:
        # 1. Create Organization
        org_result = await session.execute(select(Organization).limit(1))
        org = org_result.scalar_one_or_none()
        if not org:
            org = Organization(name="Cardiology Wing")
            session.add(org)
            await session.flush()

        # 2. Create Test Doctor
        user_result = await session.execute(select(User).where(User.email == TEST_EMAIL))
        doctor = user_result.scalar_one_or_none()
        if not doctor:
            doctor = User(
                email=TEST_EMAIL,
                password_hash=hash_password(TEST_PASSWORD),
                full_name=pii_encryption.encrypt("Dr. Sarah Mitchell"),
                role="doctor",
                # REMOVED department_role and staff_status from here
                organization_id=org.id,
                email_verified=True
            )
            session.add(doctor)
            await session.flush()

        # 3. Create a Patient
        pat_result = await session.execute(select(Patient).where(Patient.organization_id == org.id).limit(1))
        patient = pat_result.scalar_one_or_none()
        if not patient:
            patient = Patient(
                organization_id=org.id,
                full_name=pii_encryption.encrypt("John Doe"),
                date_of_birth=pii_encryption.encrypt("1980-01-01"),
                mrn="MRN-12345",
                gender="Male"
            )
            session.add(patient)
            await session.flush()

        # 4. Create Consultations (Approval Queue & Metrics)
        now = datetime.now(timezone.utc)
        
        # Pending Review
        session.add(Consultation(
            doctor_id=doctor.id, patient_id=patient.id, organization_id=org.id,
            scheduled_at=now - timedelta(hours=2),
            visit_state="Needs Review", urgency_level="high", status="completed"
        ))
        # Cleared Today
        session.add(Consultation(
            doctor_id=doctor.id, patient_id=patient.id, organization_id=org.id,
            scheduled_at=now - timedelta(hours=4), completion_time=now,
            visit_state="Signed", urgency_level="normal", status="completed"
        ))
        
        # 5. Create Task (Unsigned Orders)
        session.add(Task(
            doctor_id=doctor.id, title="Sign Lab Order", priority="urgent", status="pending"
        ))

        # 6. Create Staff Shift (Calendar Event)
        session.add(CalendarEvent(
            user_id=doctor.id, organization_id=org.id, event_type="custom",
            title="Morning Shift", start_time=now.replace(hour=8, minute=0),
            end_time=now.replace(hour=16, minute=0), all_day=False, status="scheduled"
        ))

        # 7. Create Pending Invite
        random_id = uuid.uuid4().hex[:8] # Generate a short random string
        session.add(Invitation(
            email=f"nurse_{random_id}@saramedico.com", 
            role="patient", 
            department_role="Head Nurse",
            token_hash=f"hash_{random_id}", # Ensures this is always unique
            expires_at=now + timedelta(hours=48),
            organization_id=org.id, 
            created_by_id=doctor.id, 
            status="pending"
        ))

        await session.commit()
        print("Database seeding completed successfully.")


async def test_endpoints():
    print("\n--- 1. Authenticating ---")
    async with httpx.AsyncClient(timeout=10.0) as client:
        login_resp = await client.post(f"{BASE_URL}/auth/login", json={
            "email": TEST_EMAIL, "password": TEST_PASSWORD
        })
        
        if login_resp.status_code != 200:
            print(f"Login Failed: {login_resp.text}")
            return
            
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("Authenticated successfully.")

        # --- Test 1: Queue Metrics ---
        print("\n--- 2. GET /consultations/queue/metrics ---")
        resp = await client.get(f"{BASE_URL}/consultations/queue/metrics", headers=headers)
        print(f"Status: {resp.status_code}")
        print(json.dumps(resp.json(), indent=2) if resp.status_code == 200 else resp.text)

        # --- Test 2: Doctor Dashboard Metrics ---
        print("\n--- 3. GET /doctor/me/dashboard ---")
        resp = await client.get(f"{BASE_URL}/doctor/me/dashboard", headers=headers)
        print(f"Status: {resp.status_code}")
        print(json.dumps(resp.json(), indent=2) if resp.status_code == 200 else resp.text)

        # --- Test 3: Filtered Approval Queue List ---
        print("\n--- 4. GET /consultations (Approval Queue Filtered) ---")
        resp = await client.get(f"{BASE_URL}/consultations?visit_state=Needs Review", headers=headers)
        print(f"Status: {resp.status_code}")
        print(json.dumps(resp.json(), indent=2) if resp.status_code == 200 else resp.text)

        # --- Test 4: Staff Roster ---
        print("\n--- 5. GET /team/staff ---")
        resp = await client.get(f"{BASE_URL}/team/staff", headers=headers)
        print(f"Status: {resp.status_code}")
        print(json.dumps(resp.json(), indent=2) if resp.status_code == 200 else resp.text)

        # --- Test 5: Pending Invites ---
        print("\n--- 6. GET /team/invites/pending ---")
        resp = await client.get(f"{BASE_URL}/team/invites/pending", headers=headers)
        print(f"Status: {resp.status_code}")
        print(json.dumps(resp.json(), indent=2) if resp.status_code == 200 else resp.text)

        # --- Test 6: Shift Schedule ---
        print("\n--- 7. GET /calendar/organization/events (Shifts) ---")
        now = datetime.now(timezone.utc)
        start_str = (now - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        end_str = (now + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        resp = await client.get(
            f"{BASE_URL}/calendar/organization/events?start_date={start_str}&end_date={end_str}&event_type=custom", 
            headers=headers
        )
        print(f"Status: {resp.status_code}")
        print(json.dumps(resp.json(), indent=2) if resp.status_code == 200 else resp.text)

async def main():
    # 1. Seed the data
    await seed_database()
    # 2. Test the endpoints
    await test_endpoints()

if __name__ == "__main__":
    asyncio.run(main())