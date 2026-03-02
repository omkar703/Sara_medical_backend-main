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
from app.models.activity_log import ActivityLog
from app.core.security import hash_password, pii_encryption

BASE_URL = "http://localhost:8000/api/v1"
TEST_EMAIL = "hospital_admin@saramedico.com"
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

        # 2. Create Test Hospital Manager (Role: 'hospital')
        user_result = await session.execute(select(User).where(User.email == TEST_EMAIL))
        manager = user_result.scalar_one_or_none()
        if not manager:
            manager = User(
                email=TEST_EMAIL,
                password_hash=hash_password(TEST_PASSWORD),
                full_name=pii_encryption.encrypt("Dr. Sarah Smith"),
                role="hospital", # Ensure role is 'hospital' to test the new permission fix
                organization_id=org.id,
                email_verified=True
            )
            session.add(manager)
            await session.flush()

        # 3. Create a Patient
        pat_result = await session.execute(select(Patient).where(Patient.organization_id == org.id).limit(1))
        patient = pat_result.scalar_one_or_none()
        if not patient:
            patient = Patient(
                organization_id=org.id,
                full_name=pii_encryption.encrypt("John Von"),
                date_of_birth=pii_encryption.encrypt("1980-01-01"),
                mrn="MRN-12345",
                gender="Male"
            )
            session.add(patient)
            await session.flush()

        now = datetime.now(timezone.utc)
        
        # 4. Create Consultations (Approval Queue)
        session.add(Consultation(
            doctor_id=manager.id, patient_id=patient.id, organization_id=org.id,
            scheduled_at=now - timedelta(hours=2),
            visit_state="Needs Review", urgency_level="high", status="completed"
        ))
        
        # 5. Create Staff Shift (Calendar Event for the Organization)
        session.add(CalendarEvent(
            user_id=manager.id, organization_id=org.id, event_type="custom",
            title="Morning Shift - Cardiology", start_time=now.replace(hour=8, minute=0),
            end_time=now.replace(hour=16, minute=0), all_day=False, status="scheduled"
        ))

        # 6. Create Pending Invite
        random_id = uuid.uuid4().hex[:8]
        session.add(Invitation(
            email=f"dr.von_{random_id}@saramedico.com", 
            role="doctor", 
            department_role="Senior Physician",
            token_hash=f"hash_{random_id}",
            expires_at=now + timedelta(hours=48),
            organization_id=org.id, 
            created_by_id=manager.id, 
            status="pending"
        ))

        # 7. Create an Audit/Activity Log to test the Audit Endpoint
        session.add(ActivityLog(
            user_id=manager.id,
            organization_id=org.id,
            activity_type="Role Permission Updated",
            description="Updated permissions for Dr. Rex Hex",
            status="success"
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
        print("Authenticated successfully as Hospital Manager.")

        # --- Test 1: Staff Roster ---
        print("\n--- 2. GET /team/staff (Roles & Permissions UI) ---")
        resp = await client.get(f"{BASE_URL}/team/staff", headers=headers)
        print(f"Status: {resp.status_code}")
        print(json.dumps(resp.json(), indent=2) if resp.status_code == 200 else resp.text)

        # --- Test 2: Pending Invites ---
        print("\n--- 3. GET /team/invites/pending (Invite Staff UI) ---")
        resp = await client.get(f"{BASE_URL}/team/invites/pending", headers=headers)
        print(f"Status: {resp.status_code}")
        print(json.dumps(resp.json(), indent=2) if resp.status_code == 200 else resp.text)

        # --- Test 3: Organization Schedule (The newly added endpoint) ---
        print("\n--- 4. GET /calendar/organization/events (Shift Schedule UI) ---")
        now = datetime.now(timezone.utc)
        start_str = (now - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
        end_str = (now + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
        resp = await client.get(
            f"{BASE_URL}/calendar/organization/events?start_date={start_str}&end_date={end_str}", 
            headers=headers
        )
        print(f"Status: {resp.status_code} (Should be 200 now)")
        print(json.dumps(resp.json()[:2], indent=2) if resp.status_code == 200 else resp.text)

        # --- Test 4: Audit Logs (The newly fixed permissions) ---
        print("\n--- 5. GET /audit/logs (Audit Logs UI) ---")
        resp = await client.get(f"{BASE_URL}/audit/logs?limit=5", headers=headers)
        print(f"Status: {resp.status_code} (Should be 200, not 403 Forbidden)")
        print(json.dumps(resp.json(), indent=2) if resp.status_code == 200 else resp.text)

async def main():
    await seed_database()
    await test_endpoints()

if __name__ == "__main__":
    asyncio.run(main())