import asyncio
from sqlalchemy import select
from app.database import async_session_maker
from app.models.appointment import Appointment

async def main():
    async with async_session_maker() as session:
        query = select(Appointment).where(Appointment.status == 'accepted').order_by(Appointment.created_at.desc()).limit(5)
        result = await session.execute(query)
        appointments = result.scalars().all()
        for appt in appointments:
            print(f"ID: {appt.id}, Zoom Link: {appt.join_url}, Meet Link: {appt.meet_link}")

if __name__ == "__main__":
    asyncio.run(main())
