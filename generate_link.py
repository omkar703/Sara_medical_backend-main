import asyncio
from datetime import datetime
from app.services.google_meet_service import google_meet_service
from app.api.deps import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import SessionLocal
from app.models.appointment import Appointment
from sqlalchemy import select

async def main():
    print("Generating real meet link via GoogleMeetService...")
    try:
        # Create a real meeting using the provided credentials
        google_event_id, meet_link = await google_meet_service.create_meeting(
            start_time=datetime.utcnow(),
            duration_minutes=30,
            summary="Emergency Test Fix Consultation",
            attendees=["test@example.com"]
        )
        print(f"Generated successfully! Link: {meet_link}")
        
        # Now apply this link to appointments that have accepted/scheduled status but no link
        async with SessionLocal() as db:
            result = await db.execute(select(Appointment).where(Appointment.status == 'accepted', Appointment.meet_link.is_(None)))
            appointments = result.scalars().all()
            for appt in appointments:
                print(f"Fixing appt {appt.id}")
                appt.meet_link = meet_link
                appt.google_event_id = google_event_id
                
            await db.commit()
            print("Successfully updated appointments with real Google Meet link!")

    except Exception as e:
        print(f"Error: {e}")

asyncio.run(main())
