
import asyncio
import sys
import os
import secrets
from datetime import datetime

# Add app to path
sys.path.append(os.getcwd())

from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.database import AsyncSessionLocal
from app.models.user import User, Organization
from app.core.security import hash_password, pii_encryption

async def seed_data():
    print("Beginning seeding process...")
    async with AsyncSessionLocal() as session:
        # Check if organization exists
        result = await session.execute(select(Organization).where(Organization.name == "Test Clinic"))
        org = result.scalar_one_or_none()
        
        if not org:
            print("Creating organization...")
            org = Organization(
                name="Test Clinic",
                subscription_tier="enterprise",
                subscription_status="active"
            )
            session.add(org)
            await session.commit()
            await session.refresh(org)
            print(f"Organization created: {org.id}")
        else:
            print(f"Organization exists: {org.id}")
        
        # Check/Create Doctor
        result = await session.execute(select(User).where(User.email == "doctor@test.com"))
        doctor = result.scalar_one_or_none()
        
        if not doctor:
            print("Creating doctor...")
            doctor = User(
                email="doctor@test.com",
                password_hash=hash_password("test123"),
                full_name=pii_encryption.encrypt("Dr. Test User"),
                role="doctor",
                organization_id=org.id,
                email_verified=True,
                phone_number=pii_encryption.encrypt("+1234567890"),
                specialty="General Practice",
                license_number=pii_encryption.encrypt("MD12345")
            )
            session.add(doctor)
            await session.commit()
            print("Doctor created")
        else:
            print("Doctor exists")
            
        # Check/Create Patient
        result = await session.execute(select(User).where(User.email == "patient@test.com"))
        patient = result.scalar_one_or_none()
        
        if not patient:
            print("Creating patient...")
            patient = User(
                email="patient@test.com",
                password_hash=hash_password("test123"),
                full_name=pii_encryption.encrypt("Test Patient"),
                role="patient",
                organization_id=org.id,
                email_verified=True,
                phone_number=pii_encryption.encrypt("+1987654321")
            )
            session.add(patient)
            await session.commit()
            print("Patient created")
        else:
            print("Patient exists")

        # Check/Create Admin
        result = await session.execute(select(User).where(User.email == "admin@test.com"))
        admin = result.scalar_one_or_none()
        
        if not admin:
            print("Creating admin...")
            admin = User(
                email="admin@test.com",
                password_hash=hash_password("test123"),
                full_name=pii_encryption.encrypt("Test Admin"),
                role="admin",
                organization_id=org.id,
                email_verified=True,
            )
            session.add(admin)
            await session.commit()
            print("Admin created")
        else:
            print("Admin exists")

        # Check/Create Hospital Admin
        result = await session.execute(select(User).where(User.email == "hospital@test.com"))
        hospital = result.scalar_one_or_none()
        
        if not hospital:
            print("Creating hospital admin...")
            hospital = User(
                email="hospital@test.com",
                password_hash=hash_password("test123"),
                full_name=pii_encryption.encrypt("Test Hospital"),
                role="hospital",
                organization_id=org.id,
                email_verified=True,
            )
            session.add(hospital)
            await session.commit()
            print("Hospital admin created")
        else:
            print("Hospital admin exists")

if __name__ == "__main__":
    asyncio.run(seed_data())
