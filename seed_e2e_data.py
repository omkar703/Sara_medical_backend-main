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
# Connects to Docker Database (Port 5435)
DB_URL = "postgresql+asyncpg://saramedico_user:SaraMed1c0_Dev_2024!Secure@localhost:5435/saramedico_dev"

engine = create_async_engine(DB_URL, echo=False)
SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def seed():
    # 1. Force Create Tables (Ensures all new tables exist)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        print(f"⚠️ Warning during table creation: {e}")

    async with SessionLocal() as db:
        print(f"🌱 Seeding Master Data to {DB_URL}...")

        # -----------------------------------------------------
        # 1. USERS & ORGANIZATION
        # -----------------------------------------------------
        org_id = uuid.uuid4()
        org = Organization(id=org_id, name="E2E Global Clinic")
        db.add(org)
        await db.flush()
        
        # Doctor
        doctor_id = uuid.uuid4()
        doctor_email = f"doctor_{uuid.uuid4().hex[:4]}@test.com"
        doctor = User(
            id=doctor_id,
            email=doctor_email, 
            password_hash=hash_password("Password123"),
            full_name=pii_encryption.encrypt("Dr. Gregory House"),
            role="doctor",
            specialty="Diagnostic Medicine",
            organization_id=org_id,
            email_verified=True
        )
        db.add(doctor)
        
        # Patient
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
            date_of_birth=pii_encryption.encrypt("1985-05-20"), # 40 Years Old
            gender="male",
            phone_number=pii_encryption.encrypt("+123456789"),
            # Mocking JSON fields for Dashboard
            allergies=["Penicillin", "Peanuts"],
            medications=["Lisinopril 10mg"],
            created_by=doctor_id
        )
        db.add(patient_profile)
        await db.flush()
        
        # -----------------------------------------------------
        # 2. HEALTH METRICS (Vitals)
        # -----------------------------------------------------
        # Old Reading
        db.add(HealthMetric(
            patient_id=patient_uuid,
            metric_type="blood_pressure",
            value="130/85",
            unit="mmHg",
            recorded_at=datetime.utcnow() - timedelta(days=5)
        ))
        
        # Latest Reading (This should appear in Dashboard)
        db.add(HealthMetric(
            patient_id=patient_uuid,
            metric_type="blood_pressure",
            value="120/80",
            unit="mmHg",
            recorded_at=datetime.utcnow() - timedelta(minutes=15)
        ))
        db.add(HealthMetric(
            patient_id=patient_uuid,
            metric_type="heart_rate",
            value="72",
            unit="bpm",
            recorded_at=datetime.utcnow() - timedelta(minutes=15)
        ))

        # -----------------------------------------------------
        # 3. RECENT CONNECTIONS (Shortcuts)
        # -----------------------------------------------------
        # Patient sees Doctor in "My Care Team"
        db.add(RecentDoctor(
            patient_id=patient_uuid,
            doctor_id=doctor_id,
            last_visit_at=datetime.utcnow() - timedelta(days=2),
            visit_count=5
        ))

        # Doctor sees Patient in "Recent Patients"
        db.add(RecentPatient(
            doctor_id=doctor_id,
            patient_id=patient_uuid,
            last_visit_at=datetime.utcnow() - timedelta(minutes=30),
            visit_count=5
        ))

        # -----------------------------------------------------
        # 4. APPOINTMENTS & CONSULTATIONS
        # -----------------------------------------------------
        # Future Appointment (Scheduling)
        db.add(Appointment(
            doctor_id=doctor_id,
            patient_id=patient_uuid,
            requested_date=datetime.utcnow() + timedelta(days=7),
            reason="Follow-up checkup",
            status="accepted"
        ))

        # Past Completed Consultation (History & Search)
        # This provides data for:
        # - GET /doctors/{id}/history
        # - GET /doctors/{id}/search
        # - GET /patients/{id}/details (Last Consultation widget)
        consultation = Consultation(
            id=uuid.uuid4(),
            doctor_id=doctor_id,
            patient_id=patient_uuid,
            organization_id=org_id,
            scheduled_at=datetime.utcnow() - timedelta(days=2),
            status="completed",
            
            # Rich Data for Search
            diagnosis="Acute Viral Pharyngitis",
            prescription="1. Paracetamol 500mg SOS\n2. Warm Saline Gargles\n3. Azithromycin 500mg OD for 3 days",
            notes="Patient presented with sore throat and mild fever. No difficulty breathing.",
            
            # JSON SOAP Note
            soap_note={
                "subjective": "Patient complains of throat pain for 2 days, worse when swallowing.",
                "objective": "Throat redness observed. Tonsils slightly inflamed. Temp 99.5F.",
                "assessment": "Likely viral infection given lack of exudate.",
                "plan": "Symptomatic relief. Monitor for 48 hours."
            },
            duration_minutes=15
        )
        db.add(consultation)
        
        await db.commit()
        
        # -----------------------------------------------------
        # REPORT
        # -----------------------------------------------------
        print("\n" + "="*50)
        print("✅ MASTER SEED SUCCESSFUL")
        print("="*50)
        print(f"🏥 Org:       E2E Global Clinic")
        print(f"👨‍⚕️ Doctor:    {doctor_email}")
        print(f"👤 Patient:   {patient_email}")
        print("-" * 50)
        print(f"🔑 DOCTOR ID:  {doctor_id}")
        print(f"🔑 PATIENT ID: {patient_uuid}") 
        print("="*50)
        print("🚀 API ENDPOINTS TO TEST:")
        print(f"1. Doctor History:   GET /api/v1/doctors/{doctor_id}/history")
        print(f"2. Doctor Search:    GET /api/v1/doctors/{doctor_id}/search?q=throat")
        print(f"3. Recent Patients:  GET /api/v1/doctors/{doctor_id}/recent-patients")
        print(f"4. Patient Details:  GET /api/v1/patients/{patient_uuid}/details")
        print(f"5. Patient Health:   GET /api/v1/patients/{patient_uuid}/health")
        print("="*50)

if __name__ == "__main__":
    try:
        asyncio.run(seed())
    except Exception as e:
        print(f"❌ Error: {e}")