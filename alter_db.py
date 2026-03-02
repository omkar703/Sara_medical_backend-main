import asyncio
from sqlalchemy import text
from app.database import engine

async def main():
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE appointments ADD COLUMN meeting_id VARCHAR(255);"))
            await conn.execute(text("ALTER TABLE appointments ADD COLUMN join_url TEXT;"))
            await conn.execute(text("ALTER TABLE appointments ADD COLUMN start_url TEXT;"))
            await conn.execute(text("ALTER TABLE appointments ADD COLUMN meeting_password VARCHAR(255);"))
            print("Columns added successfully!")
        except Exception as e:
            print(f"Error (already exists?): {e}")

if __name__ == "__main__":
    asyncio.run(main())
