import asyncio
import random
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.user import User, Organization
from app.models.appointment import Appointment
from app.models.calendar_event import CalendarEvent
from app.core.security import PIIEncryption

async def seed_calendar_appointments():
    print("📅 Starting Database Seeding for Calendar Appointments...")
    pii_encryption = PIIEncryption()
    
    async with AsyncSessionLocal() as session:
        # 1. Get the Metro City organization
        org_name = "Metro City General Hospital"
        result = await session.execute(select(Organization).where(Organization.name == org_name))
        org = result.scalar_one_or_none()
        
        if not org:
            print("❌ Organization not found. Please run seed_hospital_dashboard.py first.")
            return

        # 2. Get doctors
        doc_result = await session.execute(select(User).where(User.organization_id == org.id, User.role == "doctor"))
        doctors = doc_result.scalars().all()

        if not doctors:
            print("❌ Doctors not found. Please run seed_hospital_dashboard.py first.")
            return

        # 3. Get or Create a Patient User (since Appointment.patient_id maps to users.id)
        pat_result = await session.execute(select(User).where(User.role == "patient"))
        patient_user = pat_result.scalars().first()

        if not patient_user:
            print("👤 Creating a dummy Patient User for the appointments...")
            patient_user = User(
                email=f"dummy.patient.{uuid.uuid4().hex[:6]}@demo.com",
                password_hash="mock_hash",
                full_name=pii_encryption.encrypt("Jane Doe"),
                role="patient",
                organization_id=org.id,
                email_verified=True
            )
            session.add(patient_user)
            await session.flush()

        print("👨‍⚕️ Generating events for March 2026...")

        # Base date: March 1, 2026 (UTC)
        start_date = datetime(2026, 3, 1, tzinfo=timezone.utc)

        # Generate 20 appointments across the month
        for i in range(20):
            doctor = random.choice(doctors)
            
            # Pick a random day in March (0 to 30) and time (9 AM to 4 PM)
            day_offset = random.randint(0, 30)
            hour = random.randint(9, 16) 
            
            appt_start = start_date + timedelta(days=day_offset, hours=hour)
            appt_end = appt_start + timedelta(minutes=30)
            
            # Decrypt names for the calendar event titles safely
            try:
                doc_name = pii_encryption.decrypt(doctor.full_name)
            except Exception:
                doc_name = "Unknown Doctor"
                
            try:
                pat_name = pii_encryption.decrypt(patient_user.full_name)
            except Exception:
                pat_name = "Unknown Patient"

            # 4. Create the actual Appointment Record (using correct schema fields)
            appointment = Appointment(
                patient_id=patient_user.id,
                doctor_id=doctor.id,
                requested_date=appt_start,
                status=random.choice(["pending", "accepted", "completed"]),
                reason="Routine checkup and follow-up",
                meet_link=f"https://meet.google.com/mock-{uuid.uuid4().hex[:6]}"
            )
            session.add(appointment)
            await session.flush() # Flush to generate the appointment.id
            
            # 5. Create the Doctor's Calendar Event
            doc_event = CalendarEvent(
                user_id=doctor.id,
                organization_id=org.id,
                title=f"Appointment with {pat_name}",
                description="Routine checkup",
                start_time=appt_start,
                end_time=appt_end,
                all_day=False,
                event_type="appointment",
                appointment_id=appointment.id,
                color="#3B82F6", # System default blue for appointments
                status="scheduled"
            )
            session.add(doc_event)
            
        await session.commit()
        print("✅ Successfully generated 20 dummy calendar appointments for March 2026!")

if __name__ == "__main__":
    asyncio.run(seed_calendar_appointments())