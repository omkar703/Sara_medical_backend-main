import asyncio
import uuid
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from app.database import Base 
from app.models.user import User, Organization
from app.models.patient import Patient
from app.core.security import hash_password, pii_encryption
from app.config import settings

DB_URL = "postgresql+asyncpg://saramedico_user:SaraMed1c0_Dev_2024!Secure@postgres:5432/saramedico_dev"

engine = create_async_engine(DB_URL, echo=False)
SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def seed():
    async with SessionLocal() as db:
        print(f"🌱 Seeding Fixed Users...")

        # Organization
        org_id = uuid.uuid4()
        org = Organization(id=org_id, name="Test Hospital Org")
        db.add(org)
        await db.flush()

        users_to_create = [
            {"email": "doctor@test.com", "role": "doctor", "name": "Test Doctor"},
            {"email": "patient@test.com", "role": "patient", "name": "Test Patient"},
            {"email": "admin@test.com", "role": "admin", "name": "Test Admin"},
            {"email": "hospital@test.com", "role": "hospital", "name": "Test Hospital"},
        ]

        for u in users_to_create:
            # check if exists
            stmt = select(User).where(User.email == u["email"])
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()
            if not existing:
                user_id = uuid.uuid4()
                user = User(
                    id=user_id,
                    email=u["email"],
                    password_hash=hash_password("test1234"),
                    full_name=pii_encryption.encrypt(u["name"]),
                    role=u["role"],
                    organization_id=org_id,
                    email_verified=True
                )
                db.add(user)
                await db.flush()
                
                if u["role"] == "patient":
                    patient_profile = Patient(
                        id=user_id,
                        mrn="MRN-" + str(uuid.uuid4().hex[:6]),
                        organization_id=org_id,
                        full_name=pii_encryption.encrypt(u["name"]),
                        date_of_birth=pii_encryption.encrypt("1990-01-01"),
                        gender="other",
                        created_by=user_id # doesn't matter much
                    )
                    db.add(patient_profile)
        
        await db.commit()
        print("✅ Seeded specified users successfully.")

if __name__ == "__main__":
    asyncio.run(seed())
