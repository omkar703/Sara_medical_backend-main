import asyncio
import sys
import os
from sqlalchemy.future import select
from app.database import AsyncSessionLocal
from app.models.user import User, Organization
from app.models.patient import Patient
from app.core.security import pii_encryption

async def fix_patient():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == "patient@test.com"))
        patient = result.scalar_one_or_none()
        if patient:
            # Check if patient record exists
            record_res = await session.execute(select(Patient).where(Patient.id == patient.id))
            if not record_res.scalar_one_or_none():
                print("Missing Patient record, creating...")
                patient_record = Patient(
                    id=patient.id,
                    organization_id=patient.organization_id,
                    full_name=patient.full_name,
                    email=patient.email,
                    phone_number=patient.phone_number,
                    gender="male",
                    date_of_birth=pii_encryption.encrypt("1990-01-01"),
                    mrn="MRN-TEST-001",
                    medical_history=pii_encryption.encrypt("No known issues")
                )
                session.add(patient_record)
                await session.commit()
                print("Successfully created Patient table record.")
            else:
                print("Patient record exists")

if __name__ == "__main__":
    asyncio.run(fix_patient())
