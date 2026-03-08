import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
import os
from dotenv import load_dotenv
from uuid import UUID

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

from app.models.user import User
from app.api.v1.hospital import get_hospital_doctors_status

async def main():
    async with async_session() as db:
        result = await db.execute(select(User).where(User.email == 'soham@gmail.com').limit(1))
        target_doc = result.scalar_one_or_none()
        if not target_doc:
            print("soham@gmail.com not found")
            return
            
        print(f"Using organization_id: {target_doc.organization_id}")
        target_doc.role = 'hospital'
        try:
            response = await get_hospital_doctors_status(
                current_user=target_doc,
                organization_id=target_doc.organization_id,
                db=db
            )
            print("ACTIVE DOCTORS:")
            for doc in response.active_doctors:
                print(f"  Name: '{doc.name}', email: '{doc.email}'")
            print("INACTIVE DOCTORS:")
            for doc in response.inactive_doctors:
                print(f"  Name: '{doc.name}', email: '{doc.email}'")
        except Exception as e:
            print(f"Error calling API: {e}")

asyncio.run(main())
