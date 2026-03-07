import asyncio
import random
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.user import User, Organization, Invitation
from app.models.patient import Patient
from app.models.consultation import Consultation
from app.core.security import hash_password, pii_encryption

async def seed_dashboard_data():
    print("🚀 Starting Database Seeding for Hospital Dashboard...")
    
    async with AsyncSessionLocal() as session:
        # 1. Create a Target Organization (Hospital)
        org_name = "Urban City General Hospital"
        result = await session.execute(select(Organization).where(Organization.name == org_name))
        org = result.scalar_one_or_none()
        
        if not org:
            org = Organization(name=org_name)
            session.add(org)
            await session.flush()
            print(f"✅ Created Organization: {org_name}")

        # 2. Create the Hospital Manager
        admin_email = "admin@urbancity2.com"
        result = await session.execute(select(User).where(User.email == admin_email))
        admin = result.scalar_one_or_none()
        
        if not admin:
            admin = User(
                email=admin_email,
                password_hash=hash_password("Password123!"),
                full_name=pii_encryption.encrypt("Admin User"),
                role="hospital",
                organization_id=org.id,
                email_verified=True
            )
            session.add(admin)
            await session.flush()
            print(f"✅ Created Admin User: {admin_email}")

        # Define departments and roles for seeding
        departments = ["Cardiology", "Neurology", "General Medicine", "Pediatrics", "Emergency", "Surgery", "Orthopedics"]
        department_roles = ["Head of Department", "Senior Attending", "Attending", "Resident", "Fellow", "Consultant"]

        # 3. Create Doctors (to populate the 'totalDoctors' metric)
        print("👨‍⚕️ Generating 24 Doctors...")
        doctors = []
        for i in range(24):
            doc_email = f"doctor{i}@urbancity2.com"
            result = await session.execute(select(User).where(User.email == doc_email))
            doc = result.scalar_one_or_none()
            
            selected_dept = random.choice(departments)
            selected_role = random.choice(department_roles)
            
            if not doc:
                # Create NEW doctor with department
                doc = User(
                    email=doc_email,
                    password_hash=hash_password("Password123!"),
                    full_name=pii_encryption.encrypt(f"Dr. Test {i}"),
                    role="doctor",
                    organization_id=org.id,
                    specialty=selected_dept,  
                    department=selected_dept,
                    department_role=selected_role,
                    email_verified=True
                )
                session.add(doc)
            else:
                # UPDATE existing doctor if they are missing the department info
                if not doc.department or not doc.department_role:
                    doc.department = selected_dept
                    doc.department_role = selected_role
                    
            doctors.append(doc)
        
        if doctors:
            await session.flush()

        # 4. Create a dummy Patient (needed to schedule consultations)
        result = await session.execute(select(Patient).where(Patient.organization_id == org.id).limit(1))
        patient = result.scalar_one_or_none()
        if not patient:
            patient = Patient(
                organization_id=org.id,
                full_name=pii_encryption.encrypt("John Doe"),
                date_of_birth=pii_encryption.encrypt("1990-01-01"),
                mrn=f"MRN-{uuid.uuid4().hex[:6].upper()}",
                gender="Male"
            )
            session.add(patient)
            await session.flush()
            print("✅ Created Dummy Patient")

        # 5. Create Appointments for TODAY (to populate 'todayAppointments' metric)
        now = datetime.now(timezone.utc)
        start_of_today = now.replace(hour=8, minute=0, second=0, microsecond=0)
        
        print("📅 Generating 18 Appointments for today...")
        for i in range(18):
            # Stagger appointments throughout today
            appt_time = start_of_today + timedelta(minutes=30 * i)
            
            consultation = Consultation(
                doctor_id=admin.id if not doctors else random.choice(doctors).id,
                patient_id=patient.id,
                organization_id=org.id,
                scheduled_at=appt_time,
                duration_minutes=30,
                status="scheduled",
                visit_state="scheduled",
                urgency_level=random.choice(["normal", "high"])
            )
            session.add(consultation)

        # 6. Create Recent Activities (Staff Invitations)
        print("📨 Generating Recent Staff Invitations...")
        statuses = ["pending", "accepted", "expired"]
        for i in range(5):
            # Create activities from the last few days/hours
            created_time = now - timedelta(hours=random.randint(1, 48))
            
            invite = Invitation(
                email=f"new.staff.{i}@urbancity2.com",
                role="doctor",
                organization_id=org.id,
                created_by_id=admin.id,
                token_hash=f"mock_hash_{uuid.uuid4().hex}_{i}", # Made hash unique to avoid constraint errors
                status=random.choice(statuses),
                expires_at=now + timedelta(days=7),
                department=random.choice(departments),
                department_role=random.choice(department_roles)
            )
            session.add(invite)
            
        await session.commit()
        print("\n🎉 Seeding Complete! You can now log in with:")
        print(f"   Email:    {admin_email}")
        print(f"   Password: Password123!")
        print("   And hit your new dashboard endpoint!")

if __name__ == "__main__":
    asyncio.run(seed_dashboard_data())
