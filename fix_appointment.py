import asyncio
from datetime import datetime, timezone
from sqlalchemy import select, update
from app.database import AsyncSessionLocal
from app.models.consultation import Consultation
from app.models.user import Organization

async def fix_dates():
    async with AsyncSessionLocal() as session:
        # Get the Metro City organization
        result = await session.execute(select(Organization).where(Organization.name == "Metro City General Hospital"))
        org = result.scalar_one_or_none()
        
        if org:
            # Update all consultations for this org to be exactly right now (UTC)
            now_utc = datetime.now(timezone.utc)
            await session.execute(
                update(Consultation)
                .where(Consultation.organization_id == org.id)
                .values(scheduled_at=now_utc)
            )
            await session.commit()
            print("✅ All appointments snapped to TODAY (UTC). Refresh your dashboard!")
        else:
            print("❌ Organization not found. Run seed_hospital_dashboard.py first.")

if __name__ == "__main__":
    asyncio.run(fix_dates())