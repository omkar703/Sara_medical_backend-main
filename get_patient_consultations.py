import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://saramedico_user:SaraMed1c0_Dev_2024!Secure@localhost:5435/saramedico_dev"

settings = Settings()

import json

async def main():
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        result = await session.execute(text("SELECT id, soap_note, ai_status FROM consultations WHERE soap_note IS NOT NULL LIMIT 2"))
        rows = result.fetchall()
        for row in rows:
            print(f"ID: {row[0]}")
            print(json.dumps(row[1], indent=2))
            print("---")

asyncio.run(main())
