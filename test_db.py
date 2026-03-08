import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

from app.models.user import User
from app.core.security import pii_encryption

async def main():
    async with async_session() as db:
        result = await db.execute(select(User).where(User.role == 'doctor'))
        users = result.scalars().all()
        for u in users:
            print(f"ID: {u.id}, Email: {u.email}, encrypted_full_name: {u.full_name}")
            try:
                dec = pii_encryption.decrypt(u.full_name)
                print(f"  Decrypted: {dec}")
            except Exception as e:
                print(f"  Failed decrypting: {e}")

asyncio.run(main())
