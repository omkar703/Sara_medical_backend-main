from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user, get_organization_id
from app.database import get_db
from app.models.user import User
from app.schemas.hospital import HospitalOverviewResponse, HospitalDirectoryResponse, HospitalPatientsResponse, HospitalStaffResponse
from app.services.hospital_service import HospitalService

router = APIRouter(prefix="/hospital", tags=["Hospital Dashboard"])

@router.get("/dashboard/overview", response_model=HospitalOverviewResponse)
async def get_hospital_overview(
    current_user: User = Depends(get_current_active_user),
    organization_id: UUID = Depends(get_organization_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the high-level overview metrics and recent activities for the hospital dashboard.
    Requires 'hospital' or 'admin' role.
    """
    # Enforce role permissions securely
    if current_user.role not in ["hospital", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access the hospital dashboard."
        )

    service = HospitalService(db)
    data = await service.get_dashboard_overview(organization_id)
    
    return data

@router.get("/directory", response_model=HospitalDirectoryResponse)
async def get_hospital_directory(
    current_user: User = Depends(get_current_active_user),
    organization_id: UUID = Depends(get_organization_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the directory of all doctors and patients for the hospital.
    Requires 'hospital' or 'admin' role.
    """
    if current_user.role not in ["hospital", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access the hospital directory."
        )

    service = HospitalService(db)
    data = await service.get_hospital_directory(organization_id)
    
    return data

@router.get("/patients", response_model=HospitalPatientsResponse)
async def get_hospital_patients_section(
    current_user: User = Depends(get_current_active_user),
    organization_id: UUID = Depends(get_organization_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the patients section metrics and table data (including last visit).
    Requires 'hospital' or 'admin' role.
    """
    if current_user.role not in ["hospital", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access the hospital patients view."
        )

    service = HospitalService(db)
    data = await service.get_hospital_patients_overview(organization_id)
    
    return data

@router.get("/staff", response_model=HospitalStaffResponse)
async def get_hospital_staff_section(
    current_user: User = Depends(get_current_active_user),
    organization_id: UUID = Depends(get_organization_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the staff management metrics and detailed table data.
    Requires 'hospital' or 'admin' role.
    """
    if current_user.role not in ["hospital", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access the hospital staff view."
        )

    service = HospitalService(db)
    data = await service.get_hospital_staff(organization_id)
    
    return data