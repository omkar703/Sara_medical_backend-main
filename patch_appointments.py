import asyncio
from sqlalchemy import select, update
from app.database import AsyncSessionLocal
from app.models.appointment import Appointment

async def main():
    async with AsyncSessionLocal() as session:
        query = update(Appointment).where(
            Appointment.status == 'accepted',
            Appointment.join_url.is_(None)
        ).values(
            join_url='https://example.com/meet/test',
            start_url='https://example.com/meet/test'
        )
        await session.execute(query)
        await session.commit()
        print("Updated old appointments with placeholder zoom links.")

if __name__ == "__main__":
    asyncio.run(main())
