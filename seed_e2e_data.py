import asyncio
import uuid
import sys
import os
from datetime import datetime, timedelta

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.database import Base 
# Models
from app.models.user import User, Organization
from app.models.patient import Patient
from app.models.appointment import Appointment
from app.models.activity_log import ActivityLog
from app.models.consultation import Consultation
from app.models.health_metric import HealthMetric 
from app.models.recent_doctors import RecentDoctor
from app.models.recent_patients import RecentPatient
# Security
from app.core.security import hash_password, pii_encryption
from app.config import settings

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
DB_URL = "postgresql+asyncpg://saramedico_user:SaraMed1c0_Dev_2024!Secure@localhost:5435/saramedico_dev"

engine = create_async_engine(DB_URL, echo=False)
SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def seed():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        print(f"⚠️ Warning: {e}")

    async with SessionLocal() as db:
        print(f"🌱 Seeding Searchable Data...")

        # 1. Organization
        org_id = uuid.uuid4()
        org = Organization(id=org_id, name="E2E Global Clinic")
        db.add(org)
        await db.flush()
        
        # 2. Main Doctor (Dr. House)
        doc1_id = uuid.uuid4()
        doc1 = User(
            id=doc1_id,
            email=f"house_{uuid.uuid4().hex[:4]}@test.com", 
            password_hash=hash_password("Password123"),
            full_name=pii_encryption.encrypt("Dr. Gregory House"),
            role="doctor",
            specialty="Diagnostic Medicine",
            organization_id=org_id,
            email_verified=True
        )
        db.add(doc1)
        
        # 3. Extra Doctor 1 (Dr. Cuddy)
        doc2 = User(
            id=uuid.uuid4(),
            email=f"cuddy_{uuid.uuid4().hex[:4]}@test.com", 
            password_hash=hash_password("Password123"),
            full_name=pii_encryption.encrypt("Dr. Lisa Cuddy"),
            role="doctor",
            specialty="Endocrinology", 
            organization_id=org_id,
            email_verified=True
        )
        db.add(doc2)
        
        # 4. Extra Doctor 2 (Dr. Wilson)
        doc3 = User(
            id=uuid.uuid4(),
            email=f"wilson_{uuid.uuid4().hex[:4]}@test.com", 
            password_hash=hash_password("Password123"),
            full_name=pii_encryption.encrypt("Dr. James Wilson"),
            role="doctor",
            specialty="Oncology", 
            organization_id=org_id,
            email_verified=True
        )
        db.add(doc3)

        # 5. Patient
        patient_uuid = uuid.uuid4()
        patient_email = f"patient_{uuid.uuid4().hex[:4]}@test.com"
        patient_user = User(
            id=patient_uuid,
            email=patient_email, 
            password_hash=hash_password("Password123"),
            full_name=pii_encryption.encrypt("Daniel Benjamin"),
            role="patient",
            organization_id=org_id,
            email_verified=True
        )
        db.add(patient_user)
        
        # Add basic profile
        patient_profile = Patient(
            id=patient_uuid,
            mrn="MRN-" + str(uuid.uuid4().hex[:6]),
            organization_id=org_id,
            full_name=pii_encryption.encrypt("Daniel Benjamin"),
            date_of_birth=pii_encryption.encrypt("1985-05-20"),
            gender="male",
            created_by=doc1_id
        )
        db.add(patient_profile)
        
        await db.commit()
        
        print("\n" + "="*50)
        print("✅ SEED SUCCESSFUL")
        print("="*50)
        print(f"🔍 Added 3 Doctors for Search Testing:")
        print(f"   1. Dr. Gregory House (Diagnostic Medicine)")
        print(f"   2. Dr. Lisa Cuddy (Endocrinology)")
        print(f"   3. Dr. James Wilson (Oncology)")
        print(f"👤 Patient: {patient_email}")
        print("-" * 50)
        print(f"👉 Test Search by Name:      GET /api/v1/doctors/directory?query=Lisa")
        print(f"👉 Test Search by Specialty: GET /api/v1/doctors/directory?specialty=Oncology")
        print("="*50)

if __name__ == "__main__":
    asyncio.run(seed())