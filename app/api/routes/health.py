"""
Health Check Endpoint
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime
import redis

from app.models.schemas import HealthResponse
from app.config import get_settings
from app.workers.celery_worker import celery_app

settings = get_settings()
router = APIRouter()


def check_redis_connection() -> str:
    """Check Redis connectivity"""
    try:
        r = redis.from_url(settings.redis_url, decode_responses=True)
        r.ping()
        return "connected"
    except Exception:
        return "disconnected"


def check_celery_workers() -> str:
    """Check if Celery workers are running"""
    try:
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        
        if active_workers and len(active_workers) > 0:
            return "running"
        else:
            return "no workers"
    except Exception:
        return "unavailable"


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint
    
    Checks the status of:
    - Redis connection
    - Celery workers
    
    Returns:
        Health status information
    """
    redis_status = check_redis_connection()
    celery_status = check_celery_workers()
    
    # Determine overall status
    if redis_status == "connected" and celery_status in ["running", "unavailable"]:
        overall_status = "healthy"
    else:
        overall_status = "unhealthy"
    
    return HealthResponse(
        status=overall_status,
        redis=redis_status,
        celery=celery_status,
        timestamp=datetime.utcnow()
    )
