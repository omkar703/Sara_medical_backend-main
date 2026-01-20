"""
Root API Endpoint
"""
from fastapi import APIRouter
from datetime import datetime

from app.models.schemas import ServiceInfoResponse
from app.config import get_settings

settings = get_settings()
router = APIRouter()


@router.get("/", response_model=ServiceInfoResponse, tags=["Info"])
async def root():
    """
    Get service information
    
    Returns basic information about the Medical OCR API service
    """
    return ServiceInfoResponse(
        service=settings.app_name,
        version=settings.app_version,
        mode="cpu-only",
        timestamp=datetime.utcnow()
    )
