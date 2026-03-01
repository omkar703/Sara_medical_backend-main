import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.security import hash_password, verify_password
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text

DB_URL = "postgresql+asyncpg://saramedico_user:SaraMed1c0_Dev_2024!Secure@postgres:5432/saramedico_dev"
engine = create_async_engine(DB_URL, echo=False)
SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def fix():
    pwd_hash = hash_password("test1234")
    print(f"New Hash: {pwd_hash}")
    # Verify it works immediately
    assert verify_password("test1234", pwd_hash)
    
    async with SessionLocal() as db:
        await db.execute(
            text("UPDATE users SET password_hash = :hash WHERE email IN ('doctor@test.com', 'patient@test.com', 'admin@test.com', 'hospital@test.com')"),
            {"hash": pwd_hash}
        )
        await db.commit()
    print("✅ Passwords reset via raw SQL to 'test1234'")

if __name__ == "__main__":
    asyncio.run(fix())
