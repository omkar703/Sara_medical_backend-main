from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.doctor import DoctorSearchResponse, DoctorSearchItem
from app.core.security import pii_encryption

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
            full_name = "Encrypted"
            
        if query:
            if query.lower() not in full_name.lower():
                continue
        
        filtered_doctors.append(DoctorSearchItem(
            id=d.id,
            name=full_name,
            specialty=d.specialty,
            photo_url=d.avatar_url
        ))
        
    return DoctorSearchResponse(results=filtered_doctors)
