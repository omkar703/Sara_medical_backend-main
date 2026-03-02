"""Database Configuration and Session Management"""

from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.APP_DEBUG,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    pool_pre_ping=True,  # Verify connections before using
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# ── Synchronous session factory for Celery tasks ──────────────────────────────
# Celery workers run in greenlets (gevent) whose asyncpg connections carry event
# loop references. Creating a fresh asyncio loop in a background thread causes
#   RuntimeError: <loop> is attached to a different loop
# Solution: use a standard psycopg2 (sync) engine exclusively for Celery.
_sync_db_url = settings.DATABASE_URL.replace(
    "postgresql+asyncpg://", "postgresql+psycopg2://"
)
_sync_engine = create_engine(
    _sync_db_url,
    pool_size=5,
    max_overflow=2,
    pool_pre_ping=True,
)
SyncSessionLocal = sessionmaker(
    bind=_sync_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

# Base class for all models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database sessions.
    
    Usage in FastAPI:
        @app.get("/items")
        async def read_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables (for development only)"""
    from app import models  # Ensure all models are loaded
    async with engine.begin() as conn:
        # This will create all tables defined in models
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database connections"""
    await engine.dispose()
