"""Health Check Utilities"""

from typing import Dict

import redis.asyncio as redis
from minio import Minio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import AsyncSessionLocal


async def check_database() -> Dict[str, str]:
    """Check PostgreSQL database connectivity"""
    try:
        async with AsyncSessionLocal() as session:
            # Try to execute a simple query
            result = await session.execute(text("SELECT 1"))
            result.scalar()
            
            # Check for pgvector extension
            ext_result = await session.execute(
                text("SELECT installed_version FROM pg_available_extensions WHERE name = 'vector'")
            )
            pgvector_version = ext_result.scalar()
            
            return {
                "status": "connected",
                "service": "PostgreSQL",
                "pgvector": pgvector_version if pgvector_version else "not_installed"
            }
    except Exception as e:
        return {
            "status": "error",
            "service": "PostgreSQL",
            "error": str(e)
        }


async def check_redis() -> Dict[str, str]:
    """Check Redis connectivity"""
    try:
        client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        
        # Try to ping Redis
        await client.ping()
        
        # Get some info
        info = await client.info()
        
        await client.close()
        
        return {
            "status": "connected",
            "service": "Redis",
            "version": info.get("redis_version", "unknown")
        }
    except Exception as e:
        return {
            "status": "error",
            "service": "Redis",
            "error": str(e)
        }


async def check_minio() -> Dict[str, str]:
    """Check MinIO connectivity"""
    try:
        client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ROOT_USER,
            secret_key=settings.MINIO_ROOT_PASSWORD,
            secure=settings.MINIO_USE_SSL
        )
        
        # List buckets to verify connection
        buckets = client.list_buckets()
        bucket_names = [bucket.name for bucket in buckets]
        
        # Check if required buckets exist
        required_buckets = [
            settings.MINIO_BUCKET_UPLOADS,
            settings.MINIO_BUCKET_DOCUMENTS,
            settings.MINIO_BUCKET_AUDIO,
            settings.MINIO_BUCKET_AVATARS
        ]
        
        missing_buckets = [b for b in required_buckets if b not in bucket_names]
        
        return {
            "status": "connected",
            "service": "MinIO",
            "buckets": bucket_names,
            "missing_buckets": missing_buckets if missing_buckets else []
        }
    except Exception as e:
        return {
            "status": "error",
            "service": "MinIO",
            "error": str(e)
        }


async def check_all_services() -> Dict[str, any]:
    """Check all critical services"""
    db_status = await check_database()
    redis_status = await check_redis()
    minio_status = await check_minio()
    
    # Determine overall status
    all_healthy = all([
        db_status.get("status") == "connected",
        redis_status.get("status") == "connected",
        minio_status.get("status") == "connected"
    ])
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "services": {
            "database": db_status,
            "redis": redis_status,
            "minio": minio_status
        }
    }
