import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.appointment import Appointment

async def main():
    async with AsyncSessionLocal() as session:
        query = select(Appointment).where(Appointment.status == 'accepted').order_by(Appointment.created_at.desc()).limit(3)
        result = await session.execute(query)
        appointments = result.scalars().all()
        for appt in appointments:
            print(f"Status: {appt.status}")
            print(f"Join URL: {appt.join_url}")
            print(f"Meet Link: {appt.meet_link}")
            print("---")

if __name__ == "__main__":
    asyncio.run(main())
