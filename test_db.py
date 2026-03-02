import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.appointment import Appointment

async def main():
    try:
        async with AsyncSessionLocal() as session:
            query = select(Appointment).where(Appointment.status == 'accepted').order_by(Appointment.created_at.desc()).limit(1)
            result = await session.execute(query)
            appt = result.scalar_one_or_none()
            if appt:
                print(f"Appt ID: {appt.id}")
                print(f"Join URL: {appt.join_url}")
                print(f"Start URL: {appt.start_url}")
                print(f"Meet Link: {appt.meet_link}")
            else:
                print("No accepted appointments found.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
