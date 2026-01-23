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
    stmt = select(User).where(User.role == "doctor", User.deleted_at == None)
    
    if specialty:
        # Specialty is stored as unencrypted string for indexing/matching
        stmt = stmt.where(User.specialty.iloc(f"%{specialty}%") if hasattr(User.specialty, "iloc") else User.specialty.ilike(f"%{specialty}%"))
        # Using ilike for better matching
        stmt = select(User).where(User.role == "doctor", User.deleted_at == None)
        if specialty:
            stmt = stmt.where(User.specialty.ilike(f"%{specialty}%"))
    
    # Redefining to avoid confusion with the messy logic above
    stmt = select(User).where(User.role == "doctor", User.deleted_at == None)
    if specialty:
        stmt = stmt.where(User.specialty.ilike(f"%{specialty}%"))
    
    result = await db.execute(stmt)
    doctors = result.scalars().all()
    
    # Fuzzy name search (since names are encrypted, we decrypt and filter in memory for simplicity in this demo)
    # In a prod environment, we would use blind indexing or a separate search index.
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
