import asyncio
import uuid
import sys
import os
from datetime import datetime, timedelta

# Add backend to path so we can import app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.database import Base # Import Base to create tables
from app.models.user import User, Organization
from app.models.patient import Patient
from app.models.appointment import Appointment
from app.models.activity_log import ActivityLog
from app.models.consultation import Consultation
from app.models.health_metric import HealthMetric 
from app.core.security import hash_password, pii_encryption
from app.config import settings

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
# Port 5435 matches your docker-compose.yml (saramedico_postgres)
DB_URL = "postgresql+asyncpg://saramedico_user:SaraMed1c0_Dev_2024!Secure@localhost:5435/saramedico_dev"

engine = create_async_engine(DB_URL, echo=False)
SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def seed():
    # 1. Force Create Tables (Ensures health_metrics table exists)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        print(f"⚠️ Warning during table creation (might be connection issue): {e}")

    async with SessionLocal() as db:
        print(f"🌱 Seeding data to Database at {DB_URL}...")

        # 2. Create Organization
        org_id = uuid.uuid4()
        org = Organization(id=org_id, name="E2E Global Clinic")
        db.add(org)
        await db.flush()
        
        # 3. Create Doctor (Randomized Email to avoid IntegrityError)
        doctor_id = uuid.uuid4()
        doctor_email = f"doctor_{uuid.uuid4().hex[:4]}@test.com"
        doctor = User(
            id=doctor_id,
            email=doctor_email, 
            password_hash=hash_password("Password123"),
            full_name=pii_encryption.encrypt("Dr. Gregory House"),
            role="doctor",
            organization_id=org_id,
            email_verified=True
        )
        db.add(doctor)
        
        # 4. Create Patient (Randomized Email)
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
        
        patient_profile = Patient(
            id=patient_uuid,
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
        
        # 5. Add Health Metrics (The new feature)
        bp_metric = HealthMetric(
            patient_id=patient_uuid,
            metric_type="blood_pressure",
            value="120/80",
            unit="mmHg",
            notes="Normal resting BP",
            recorded_at=datetime.utcnow() - timedelta(minutes=15)
        )
        hr_metric = HealthMetric(
            patient_id=patient_uuid,
            metric_type="heart_rate",
            value="72",
            unit="bpm",
            notes="Resting heart rate",
            recorded_at=datetime.utcnow() - timedelta(minutes=15)
        )
        db.add(bp_metric)
        db.add(hr_metric)
        
        # 6. Add Appointment & Logs
        appointment = Appointment(
            doctor_id=doctor_id,
            patient_id=patient_uuid,
            requested_date=datetime.utcnow() + timedelta(hours=10),
            reason="Post-op check",
            status="accepted"
        )
        db.add(appointment)
        
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
        
        print("\n" + "="*40)
        print("✅ SEED SUCCESSFUL")
        print("="*40)
        print(f"🏥 Organization ID: {org_id}")
        print(f"👨‍⚕️ Doctor Email:    {doctor_email}")
        print(f"👤 Patient Email:   {patient_email}")
        print(f"🔑 PATIENT ID:      {patient_uuid}") 
        print("="*40)
        print(f"👉 Test API: GET /api/v1/patients/{patient_uuid}/health")
        print("="*40)

if __name__ == "__main__":
    try:
        asyncio.run(seed())
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Hint: Ensure Docker is running and port 5435 is exposed.")