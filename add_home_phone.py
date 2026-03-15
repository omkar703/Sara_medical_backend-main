import asyncio
from sqlalchemy import text
from app.database import engine

async def main():
    async with engine.begin() as conn:
        try:
            # Add home_phone to patients table
            await conn.execute(text("ALTER TABLE patients ADD COLUMN home_phone VARCHAR(500);"))
            print("home_phone column added to patients table successfully!")
        except Exception as e:
            print(f"Error (already exists?): {e}")

if __name__ == "__main__":
    asyncio.run(main())
