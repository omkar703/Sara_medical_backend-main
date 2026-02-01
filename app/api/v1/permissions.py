"""Permissions API - Grants, Revokes, and Checks"""

from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from pydantic import BaseModel

from app.database import get_db
from app.core.deps import get_current_active_user
from app.models.user import User
from app.models.data_access_grant import DataAccessGrant

router = APIRouter(prefix="/permissions", tags=["Permissions"])

# Schemas
class GrantAccessRequest(BaseModel):
    doctor_id: UUID
    ai_access_permission: bool
    access_level: str = "read_analyze" # read_only, read_analyze
    expiry_days: int = 90
    reason: Optional[str] = None

class RequestAccessRequest(BaseModel):
    patient_id: UUID
    reason: Optional[str] = None

class RevokeAccessRequest(BaseModel):
    doctor_id: UUID

class CheckPermissionResponse(BaseModel):
    success: bool
    doctor_id: UUID
    patient_id: UUID
    has_permission: bool
    ai_access_permission: bool
    message: str


@router.post("/grant-doctor-access", status_code=status.HTTP_201_CREATED)
async def grant_access(
    request: GrantAccessRequest,
    current_user: User = Depends(get_current_active_user), # Patient
    db: AsyncSession = Depends(get_db),
):
    if current_user.role != "patient":
        raise HTTPException(status_code=403, detail="Only patients can grant access.")
        
    # Check if doctor exists (optional verification)
    
    # Create or Update Grant
    # Create or Approave using Service
    from app.services.permission_service import PermissionService
    service = PermissionService(db)
    
    expires_at = datetime.now(timezone.utc) + timedelta(days=request.expiry_days)
    
    grant = await service.create_access_grant(
        doctor_id=request.doctor_id,
        patient_id=current_user.id,
        grant_reason=request.reason,
        expires_at=expires_at,
        access_level=request.access_level,
        ai_access_permission=request.ai_access_permission
    )
    
    await db.commit()
    
    # Audit Log
    from app.services.audit_service import AuditService
    audit_service = AuditService(db)
    await audit_service.log_event(
        user_id=current_user.id,
        action="permission.grant",
        resource_type="data_access_grant",
        resource_id=grant.id,
        organization_id=current_user.organization_id,
        metadata={"doctor_id": str(request.doctor_id), "ai_access": request.ai_access_permission}
    )
    
    return {"success": True, "message": "Access granted"}

@router.post("/request", status_code=status.HTTP_201_CREATED)
async def request_access(
    request: RequestAccessRequest,
    current_user: User = Depends(get_current_active_user), # Doctor
    db: AsyncSession = Depends(get_db)
):
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can request access")
        
    from app.services.permission_service import PermissionService
    service = PermissionService(db)
    
    grant = await service.request_access(
        doctor_id=current_user.id,
        patient_id=request.patient_id,
        reason=request.reason
    )
    
    await db.commit()
    
    return {"success": True, "message": "Access request sent", "status": grant.status}

@router.delete("/revoke-doctor-access")
async def revoke_access(
    request: RevokeAccessRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(DataAccessGrant).where(
        DataAccessGrant.patient_id == current_user.id,
        DataAccessGrant.doctor_id == request.doctor_id,
        DataAccessGrant.is_active == True
    )
    result = await db.execute(stmt)
    grant = result.scalars().first()
    
    if grant:
        grant.is_active = False
        grant.revoked_at = datetime.now(timezone.utc)
        await db.commit()
        
        # Audit Log
        from app.services.audit_service import AuditService
        audit_service = AuditService(db)
        await audit_service.log_event(
            user_id=current_user.id,
            action="permission.revoke",
            resource_type="data_access_grant",
            resource_id=grant.id,
            organization_id=current_user.organization_id,
            metadata={"doctor_id": str(request.doctor_id)}
        )
        
    return {"success": True, "message": "Access revoked"}

@router.get("/check", response_model=CheckPermissionResponse)
async def check_permission(
    patient_id: UUID,
    current_user: User = Depends(get_current_active_user), # Doctor
    db: AsyncSession = Depends(get_db)
):
    from app.services.permission_service import PermissionService
    service = PermissionService(db)
    
    has_perm = await service.check_doctor_access(current_user.id, patient_id)
    
    return {
        "success": has_perm,
        "doctor_id": current_user.id,
        "patient_id": patient_id,
        "has_permission": has_perm,
        "ai_access_permission": has_perm, # Placeholder pending model update
        "message": "Access granted" if has_perm else "No access"
    }
