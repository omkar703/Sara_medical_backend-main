"""Script to enable pgvector extension"""
import asyncio
from app.database import engine

async def enable_pgvector():
    async with engine.begin() as conn:
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        print("✅ pgvector extension enabled")

if __name__ == "__main__":
    asyncio.run(enable_pgvector())
