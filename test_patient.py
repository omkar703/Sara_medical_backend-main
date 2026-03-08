import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.services.patient_service import PatientService
import logging

logging.basicConfig(level=logging.INFO)

async def main():
    engine = create_async_engine(
        "postgresql+asyncpg://saramedico_user:SaraMed1c0_Dev_2024!Secure@localhost:5435/saramedico_dev",
        echo=False,
    )
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        service = PatientService(session)
        print(f"Service returned type: {type(service.create_patient)}")
        result = await session.execute(text("SELECT id FROM users LIMIT 1;"))
        uid = result.scalar_one_or_none()
        if uid:
            print("Found UID:", uid)

asyncio.run(main())
