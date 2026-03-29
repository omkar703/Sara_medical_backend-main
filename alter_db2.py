import asyncio
from sqlalchemy import text
from app.database import engine

async def main():
    async with engine.begin() as conn:
        try:
            # Adding columns
            await conn.execute(text("ALTER TABLE appointments ADD COLUMN created_by VARCHAR(50) DEFAULT 'patient' NOT NULL;"))
            await conn.execute(text("ALTER TABLE appointments ADD COLUMN scheduled_at TIMESTAMPTZ;"))
            print("Columns added successfully!")
            
            # For Postgres ENUM, adding a value:
            await conn.execute(text("ALTER TYPE appointment_status ADD VALUE 'rejected';"))
            print("Enum updated successfully!")
        except Exception as e:
            print(f"Error (already exists?): {e}")

if __name__ == "__main__":
    asyncio.run(main())
