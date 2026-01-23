"""Patient API Endpoints"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user, get_organization_id, require_doctor, require_role
from app.database import get_db
from app.models.user import User
from app.schemas.patient import (
    PatientCreate,
    PatientListResponse,
    PatientResponse,
    PatientUpdate,
)
from app.services.audit_service import log_action
from app.services.patient_service import PatientService

router = APIRouter(prefix="/patients", tags=["Patients"])


@router.get("", response_model=PatientListResponse)
async def list_patients(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    organization_id: UUID = Depends(get_organization_id),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    """
    List patients for the current user's organization.
    Supports pagination and searching by MRN (and name in future).
    """
    service = PatientService(db)
    result = await service.list_patients(
        organization_id=organization_id,
        page=page,
        limit=limit,
        search=search
    )
    
    # Audit log
    await log_action(
        db=db,
        user_id=current_user.id,
        organization_id=organization_id,
        action="list",
        resource_type="patient",
        resource_id=None,
        request=request,
        metadata={"page": page, "limit": limit, "search": search}
    )
    
    # Rename 'items' key to 'patients' to match schema alias if needed, 
    # but Pydantic alias="patients" on 'items' field handles mapping mapping if we pass 'items' to constructor.
    # Actually PatientListResponse field is `items` aliased as `patients`.
    # Service returns dict with `items`. So passing result directly works.
    
    return result


@router.post("", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    patient_in: PatientCreate,
    current_user: User = Depends(require_role("doctor")), # Or admin
    organization_id: UUID = Depends(get_organization_id),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    """
    Create a new patient record.
    Requires 'doctor' or 'admin' role.
    """
    service = PatientService(db)
    
    # Convert Pydantic model to dict
    patient_data = patient_in.model_dump(exclude_unset=True)
    
    patient = await service.create_patient(
        patient_data=patient_data,
        organization_id=organization_id,
        created_by=current_user.id
    )
    
    await db.commit()
    
    # Audit log
    await log_action(
        db=db,
        user_id=current_user.id,
        organization_id=organization_id,
        action="create",
        resource_type="patient",
        resource_id=patient["id"],
        request=request,
        metadata={"mrn": patient["mrn"]}
    )
    await db.commit() # Commit audit log
    
    return patient


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: UUID,
    current_user: User = Depends(get_current_active_user),
    organization_id: UUID = Depends(get_organization_id),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    """
    Get patient details by ID.
    Ensures patient belongs to the same organization.
    """
    service = PatientService(db)
    patient = await service.get_patient(patient_id, organization_id)
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Audit log
    await log_action(
        db=db,
        user_id=current_user.id,
        organization_id=organization_id,
        action="view",
        resource_type="patient",
        resource_id=patient_id,
        request=request
    )
    await db.commit()
    
    return patient


@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: UUID,
    patient_in: PatientUpdate,
    current_user: User = Depends(require_role("doctor")),
    organization_id: UUID = Depends(get_organization_id),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    """
    Update patient details.
    Requires 'doctor' or 'admin' role.
    """
    service = PatientService(db)
    patient_data = patient_in.model_dump(exclude_unset=True)
    
    updated_patient = await service.update_patient(
        patient_id, organization_id, patient_data
    )
    
    if not updated_patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    await db.commit()
    
    # Audit log
    await log_action(
        db=db,
        user_id=current_user.id,
        organization_id=organization_id,
        action="update",
        resource_type="patient",
        resource_id=patient_id,
        request=request,
        metadata={"updated_fields": list(patient_data.keys())}
    )
    await db.commit()
    
    return updated_patient


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(
    patient_id: UUID,
    current_user: User = Depends(require_role("admin")), # Restrict delete to admin? Or doctor too? Roadmap said doctor/admin.
    organization_id: UUID = Depends(get_organization_id),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    """
    Soft delete a patient.
    Requires 'admin' role (stricter than update).
    """
    service = PatientService(db)
    success = await service.delete_patient(patient_id, organization_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    await db.commit()
    
    # Audit log
    await log_action(
        db=db,
        user_id=current_user.id,
        organization_id=organization_id,
        action="delete",
        resource_type="patient",
        resource_id=patient_id,
        request=request
    )
    await db.commit()
    
    return None
