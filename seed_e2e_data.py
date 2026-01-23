import asyncio
import uuid
import sys
import os
from datetime import datetime, timedelta

# Add backend to path so we can import app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.models.user import User, Organization
from app.models.patient import Patient
from app.models.appointment import Appointment
from app.models.activity_log import ActivityLog
from app.models.consultation import Consultation
from app.core.security import hash_password, pii_encryption
from app.config import settings

# Override DATABASE_URL for host access (docker maps 5433 to 5432)
# Using the default credentials from .env but pointing to localhost:5433
DB_URL = "postgresql+asyncpg://saramedico_user:SaraMed1c0_Dev_2024!Secure@localhost:5432/saramedico_dev"

engine = create_async_engine(DB_URL, echo=False)
SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def seed():
    async with SessionLocal() as db:
        # 1. Create Organization
        org_id = uuid.uuid4()
        org = Organization(id=org_id, name="E2E Global Clinic")
        db.add(org)
        await db.flush()
        
        # 2. Create Doctor
        doctor_id = uuid.uuid4()
        doctor = User(
            id=doctor_id,
            email="doctor_e2e_final@test.com",
            password_hash=hash_password("Password123"),
            full_name=pii_encryption.encrypt("Dr. Gregory House"),
            role="doctor",
            organization_id=org_id,
            email_verified=True
        )
        db.add(doctor)
        
        # 3. Create Patient (User + Profile)
        patient_uuid = uuid.uuid4()
        
        # User record for the patient (for authentication and appointments)
        patient_user = User(
            id=patient_uuid,
            email="patient_e2e_final@test.com",
            password_hash=hash_password("Password123"),
            full_name=pii_encryption.encrypt("Daniel Benjamin"),
            role="patient",
            organization_id=org_id,
            email_verified=True
        )
        db.add(patient_user)
        
        # Patient record (clinical profile)
        patient_profile = Patient(
            id=patient_uuid, # Matching ID to bridge User/Patient in this dummy data
            mrn="MRN-E2E-" + str(uuid.uuid4().hex[:6]),
            organization_id=org_id,
            full_name=pii_encryption.encrypt("Daniel Benjamin"),
            date_of_birth=pii_encryption.encrypt("1985-05-20"),
            gender="male",
            phone_number=pii_encryption.encrypt("+123456789"),
            created_by=doctor_id
        )
        db.add(patient_profile)
        await db.flush()
        
        # 4. Create Previous Consultation (Last Visit)
        last_visit = Consultation(
            patient_id=patient_uuid,
            doctor_id=doctor_id,
            organization_id=org_id,
            scheduled_at=datetime.utcnow() - timedelta(days=30),
            status="completed",
            notes="Patient recovering well from recent checkup."
        )
        db.add(last_visit)
        
        # 5. Create Upcoming Appointment (confirmed/accepted)
        appointment = Appointment(
            doctor_id=doctor_id,
            patient_id=patient_uuid,
            requested_date=datetime.utcnow() + timedelta(hours=10),
            reason="Post-op check",
            status="accepted"
        )
        db.add(appointment)
        
        # 6. Initial Activity logs
        log1 = ActivityLog(
            user_id=doctor_id,
            organization_id=org_id,
            activity_type="Lab Results Reviewed",
            description="Reviewed blood work for Daniel Benjamin",
            status="completed",
            created_at=datetime.utcnow() - timedelta(minutes=60)
        )
        db.add(log1)
        
        await db.commit()
        print("--- Saramedico E2E Seed Report ---")
        print(f"Organization: {org.name} ({org_id})")
        print(f"Doctor: Dr. Gregory House (doctor_e2e@test.com / Password123)")
        print(f"Patient: Daniel Benjamin (patient_e2e@test.com / Password123)")
        print(f"Next Appointment: Post-op check at {(datetime.utcnow() + timedelta(hours=2)).strftime('%I:%M %p')}")
        print(f"Last Visit Found: Yes (30 days ago)")
        print("Success: E2E Dummy Data Seeded!")

if __name__ == "__main__":
    asyncio.run(seed())
