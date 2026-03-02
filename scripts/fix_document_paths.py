import asyncio
import uuid
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update
from app.models.document import Document
from app.config import settings

async def fix_existing_paths():
    """
    Migration script to fix documents with incorrect full filesystem paths.
    Converts '/tmp/saramedico_uploads/<uuid>.pdf' to 'saramedico_uploads/<uuid>.pdf'
    or structured paths if possible.
    """
    engine = create_async_engine(settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"))
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as db:
        # Find all documents with paths starting with /tmp
        stmt = select(Document).where(Document.storage_path.like("/tmp/%"))
        result = await db.execute(stmt)
        docs = result.scalars().all()
        
        print(f"Found {len(docs)} documents with incorrect paths.")
        
        for doc in docs:
            old_path = doc.storage_path
            # Remove leading slash to at least avoid double slash, 
            # though the file might still be missing from MinIO if it was never uploaded.
            new_path = old_path.lstrip("/")
            
            # Better: if it's /tmp/saramedico_uploads/<id><ext>, just use that part
            if "/tmp/" in old_path:
                 new_path = old_path.split("/tmp/")[1]
            
            print(f"Updating Doc {doc.id}: {old_path} -> {new_path}")
            doc.storage_path = new_path
            
        await db.commit()
        print("Done.")

if __name__ == "__main__":
    asyncio.run(fix_existing_paths())
