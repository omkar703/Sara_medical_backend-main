"""Organization Management Endpoints"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user, get_organization_id, require_role
from app.database import get_db
from app.models.user import User
from app.schemas.organization import (
    InvitationAccept,
    InvitationCreate,
    InvitationResponse,
    MemberResponse,
    OrganizationResponse,
    OrganizationUpdate,
)
from app.services.audit_service import log_action
from app.services.organization_service import OrganizationService

router = APIRouter(prefix="/organization", tags=["Organization"])


@router.get("", response_model=OrganizationResponse)
async def get_my_organization(
    current_user: User = Depends(get_current_active_user),
    organization_id: UUID = Depends(get_organization_id),
    db: AsyncSession = Depends(get_db),
):
    """Get current organization details"""
    service = OrganizationService(db)
    org = await service.get_org_details(organization_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


@router.get("/members", response_model=List[MemberResponse])
async def list_members(
    current_user: User = Depends(get_current_active_user),
    organization_id: UUID = Depends(get_organization_id),
    db: AsyncSession = Depends(get_db),
):
    """List all members of the organization"""
    # Permissions: Doctors and Admins can view team
    # Patients cannot access this endpoint (handled by role check or context)
    if current_user.role == "patient":
         raise HTTPException(status_code=403, detail="Not authorized")
         
    service = OrganizationService(db)
    members = await service.list_members(organization_id)
    
    # Decrypt names for display
    # (Assuming simple decrypt helper or model logic, duplicating decryption logic 
    # from previous phases or using a helper if available. 
    # For now, simplistic decryption on the fly or just returning objects if schemas handle it)
    
    # The MemberResponse schema expects `full_name`. The User model has it encrypted.
    # We should decrypt it.
    from app.core.security import pii_encryption
    
    results = []
    for m in members:
        try:
            m.full_name = pii_encryption.decrypt(m.full_name)
        except:
            pass # Keep as is if fail
        results.append(m)
        
    return results


@router.post("/invitations", response_model=InvitationResponse)
async def invite_member(
    invite_data: InvitationCreate,
    current_user: User = Depends(require_role("admin")), # Only admins invite
    organization_id: UUID = Depends(get_organization_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Invite a new member to the organization.
    Requires ADMIN role.
    """
    service = OrganizationService(db)
    
    invitation = await service.invite_member(
        organization_id=organization_id,
        email=invite_data.email,
        role=invite_data.role,
        created_by_id=current_user.id
    )
    
    await db.commit()
    
    # Audit
    await log_action(
        db=db,
        user_id=current_user.id,
        organization_id=organization_id,
        action="invite_member",
        resource_type="invitation",
        resource_id=invitation.id,
        metadata={"email": invite_data.email, "role": invite_data.role}
    )
    await db.commit()
    
    return invitation


@router.post("/invitations/accept", response_model=MemberResponse)
async def accept_invitation(
    accept_data: InvitationAccept,
    db: AsyncSession = Depends(get_db),
):
    """
    Accept an invitation and register.
    Public endpoint (no auth required), relies on token.
    """
    service = OrganizationService(db)
    
    user = await service.accept_invitation(
        token=accept_data.token,
        full_name=accept_data.full_name,
        password=accept_data.password,
        specialty=accept_data.specialty,
        license_number=accept_data.license_number
    )
    
    await db.commit()
    
    # Decrypt for response
    from app.core.security import pii_encryption
    try:
        user.full_name = pii_encryption.decrypt(user.full_name)
    except:
        pass
        
    return user
