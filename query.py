import asyncio
from sqlalchemy import select
from app.database import async_session
from app.models.user import User, Organization
import sys

async def main():
    try:
        async with async_session() as session:
            result = await session.execute(select(Organization.id, Organization.name))
            orgs = result.all()
            print("Organizations:")
            for o in orgs:
                print(f"  {o.id}: {o.name}")
            
            result = await session.execute(select(User.id, User.email, User.role, User.organization_id))
            users = result.all()
            print("Users:")
            for u in users:
                print(f"  {u.email} ({u.role}) -> Org: {u.organization_id}")
    except Exception as e:
        print(e)

asyncio.run(main())
