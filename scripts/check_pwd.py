import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.security import verify_password
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from app.models.user import User

DB_URL = "postgresql+asyncpg://saramedico_user:SaraMed1c0_Dev_2024!Secure@postgres:5432/saramedico_dev"
engine = create_async_engine(DB_URL, echo=False)
SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def check():
    async with SessionLocal() as db:
        stmt = select(User).where(User.email == "doctor@test.com")
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if user:
            is_valid = verify_password("test1234", user.password_hash)
            print(f"Password 'test1234' is valid for {user.email}: {is_valid}")
        else:
            print("User not found")

if __name__ == "__main__":
    asyncio.run(check())
