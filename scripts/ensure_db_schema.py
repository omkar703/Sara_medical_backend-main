import asyncio
import sys
import os

# Add the project root to sys.path to allow importing from 'app'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import engine, Base
# Import all models to ensure they're registered with Base.metadata
from app import models 

async def ensure_schema():
    print("🚀 Running direct schema check/creation...")
    try:
        async with engine.begin() as conn:
            # This will create tables that don't exist yet
            # It will NOT destroy or modify existing tables/data
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Database schema is up to date!")
    except Exception as e:
        print(f"❌ Error ensuring schema: {e}")
        # We don't exit with failure here to allow the app to try starting anyway
        # but the error is logged.

if __name__ == "__main__":
    asyncio.run(ensure_schema())
