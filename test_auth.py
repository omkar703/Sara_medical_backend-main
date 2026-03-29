import sys
import os
import asyncio
sys.path.append(os.getcwd())

from app.database import AsyncSessionLocal
from app.models.user import User
from sqlalchemy.future import select

async def main():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        print("User:", user)

if __name__ == "__main__":
    asyncio.run(main())
