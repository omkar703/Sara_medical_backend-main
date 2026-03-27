from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.core.deps import get_current_user, get_current_active_user
from app.models.user import User
from app.schemas.doctor import DoctorSearchResponse, DoctorSearchItem
from app.core.security import pii_encryption
from app.models.doctor_status import DoctorStatus
from app.schemas.doctor_status import DoctorStatusUpdateRequest, DoctorStatusResponse

router = APIRouter(prefix="/doctors", tags=["Public Directory"])

@router.get("/search", response_model=DoctorSearchResponse)
async def search_doctors(
    query: Optional[str] = Query(None, description="Search by doctor name"),
    specialty: Optional[str] = Query(None, description="Filter by specialty"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search for doctors by name or specialty.
    Available to all logged-in users.
    """
    from app.models.patient import Patient

    # If user is a patient, they can only search for the doctor who onboarded them
    onboarding_doctor_id = None
    if current_user.role == "patient":
        # Find the patient record to see who created it
        p_stmt = select(Patient).where(Patient.id == current_user.id)
        p_result = await db.execute(p_stmt)
        patient_record = p_result.scalar_one_or_none()
        if patient_record:
            onboarding_doctor_id = patient_record.created_by

    stmt = select(User).where(User.role == "doctor", User.deleted_at == None)
    
    # Apply onboarding doctor filter if applicable
    if onboarding_doctor_id:
        stmt = stmt.where(User.id == onboarding_doctor_id)

    if specialty:
        stmt = stmt.where(User.specialty.ilike(f"%{specialty}%"))
    
    result = await db.execute(stmt)
    doctors = result.scalars().all()
    
    # Fuzzy name search (since names are encrypted, we decrypt and filter in memory for simplicity in this demo)
    filtered_doctors = []
    for d in doctors:
        try:
            full_name = pii_encryption.decrypt(d.full_name)
        except:
            full_name = d.full_name or "Unknown"
            
        if query:
            if query.lower() not in full_name.lower():
                continue
        
        # Generate avatar preview URL if available
        avatar_preview = None
        if d.avatar_url:
            try:
                from app.services.minio_service import minio_service
                from app.config import settings
                avatar_preview = minio_service.generate_presigned_url(
                    bucket_name=settings.MINIO_BUCKET_AVATARS,
                    object_name=d.avatar_url
                )
            except Exception:
                pass

        filtered_doctors.append(DoctorSearchItem(
            id=d.id,
            name=full_name,
            specialty=d.specialty,
            photo_url=avatar_preview
        ))
        
    return DoctorSearchResponse(results=filtered_doctors)

@router.get("/directory", response_model=DoctorSearchResponse)
async def search_global_doctor_directory(
    query: Optional[str] = Query(None, description="Search by doctor name"),
    specialty: Optional[str] = Query(None, description="Filter by specialty"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Patient-facing Directory Search.
    Allows searching for ANY doctor in the system (unlike /search which is restricted).
    """
    # Patient can see all doctors in their same organization
    organization_id_filter = None
    if current_user.role == "patient":
        from app.models.patient import Patient
        p_stmt = select(Patient).where(Patient.id == current_user.id)
        p_result = await db.execute(p_stmt)
        patient_record = p_result.scalar_one_or_none()
        if patient_record:
            organization_id_filter = patient_record.organization_id

    # 1. Fetch active doctors
    stmt = select(User).where(User.role == "doctor", User.deleted_at.is_(None))
    
    if organization_id_filter:
        stmt = stmt.where(User.organization_id == organization_id_filter)
        
    # Filter by Specialty (Database side)
    if specialty:
        stmt = stmt.where(User.specialty.ilike(f"%{specialty}%"))
        
    result = await db.execute(stmt)
    doctors = result.scalars().all()
    
    # 2. Filter by Name (In-Memory due to encryption)
    filtered_results = []
    
    for doc in doctors:
        # Decrypt Name
        try:
            name = pii_encryption.decrypt(doc.full_name)
        except:
            name = "Unknown Doctor"
            
        # Apply Name Filter
        if query:
            if query.lower() not in name.lower():
                continue
        
        # Generate avatar preview URL if available
        avatar_preview = None
        if doc.avatar_url:
            try:
                from app.services.minio_service import minio_service
                from app.config import settings
                avatar_preview = minio_service.generate_presigned_url(
                    bucket_name=settings.MINIO_BUCKET_AVATARS,
                    object_name=doc.avatar_url
                )
            except Exception:
                pass

        filtered_results.append(DoctorSearchItem(
            id=doc.id,
            name=name,
            specialty=doc.specialty,
            photo_url=avatar_preview
        ))
        
    return DoctorSearchResponse(results=filtered_results)