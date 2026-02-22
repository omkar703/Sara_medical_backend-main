from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime, timedelta
import uuid
import hashlib

from app.database import get_db
from app.core.deps import get_current_user, get_organization_id
from app.models.user import User, Invitation
from app.models.activity_log import ActivityLog
from app.schemas.team import TeamInviteCreate, TeamRole, StaffMemberResponse, PendingInviteResponse
from app.core.security import pii_encryption

router = APIRouter(prefix="/team", tags=["Team Management"])

# Helper to generate token hash
def generate_token_hash() -> str:
    token = uuid.uuid4().hex
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    return token, token_hash

@router.post("/invite", status_code=status.HTTP_201_CREATED)
async def invite_team_member(
    invite: TeamInviteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    organization_id: UUID = Depends(get_organization_id),
):
    """Create a team invitation.
    - Checks for duplicate pending invitations.
    - Generates a secure token (hashed for storage).
    - Logs the invitation link to the console.
    - Creates an activity log entry.
    """
    if current_user.role not in {"admin", "doctor", "hospital"}:
        raise HTTPException(status_code=403, detail="Insufficient permissions to invite team members")

    # Duplicate check: pending invitation with same email in this organization
    dup_q = select(Invitation).where(
        Invitation.email == invite.email,
        Invitation.organization_id == organization_id,
        Invitation.status == "pending",
    )
    dup_res = await db.execute(dup_q)
    if dup_res.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User already invited.")

    # Create token
    token, token_hash = generate_token_hash()
    expires_at = datetime.utcnow() + timedelta(hours=48)

    # Map specification roles to database user_role enum
    role_mapping = {
        "ADMINISTRATOR": "admin",
        "MEMBER": "doctor",
        "PATIENT": "patient"
    }
    db_role = role_mapping.get(invite.role, "patient")

    new_invite = Invitation(
        email=invite.email,
        role=db_role,
        token_hash=token_hash,
        expires_at=expires_at,
        organization_id=organization_id,
        created_by_id=current_user.id,
        status="pending",
    )
    db.add(new_invite)
    await db.flush()  # get ID if needed

    # Log invitation link (mock email)
    invitation_link = f"https://example.com/invite/{token}"
    print(f"[Invitation] Link for {invite.email}: {invitation_link}")

    # Activity log entry
    activity = ActivityLog(
        user_id=current_user.id,
        organization_id=organization_id,
        activity_type="Team Invite Sent",
        description=f"Invited {invite.full_name} ({invite.email}) as {invite.role}",
        status="pending",
        extra_data={"invitation_id": str(new_invite.id), "link": invitation_link},
    )
    db.add(activity)
    await db.commit()
    await db.refresh(new_invite)
    return {"detail": "Invitation sent", "invitation_id": str(new_invite.id)}

@router.get("/roles", response_model=list[TeamRole])
async def list_team_roles(
    _: User = Depends(get_current_user),
):
    """Return static role descriptions used by the frontend."""
    roles = [
        TeamRole(role="ADMINISTRATOR", description="Manage team & billing, Full patient record access, Configure AI settings"),
        TeamRole(role="MEMBER", description="View assigned patients, Use AI diagnostic tools, No billing access"),
        TeamRole(role="PATIENT", description="Check-in appointments, Access Records, No billing access"),
    ]
    return roles

@router.get("/staff", response_model=list[StaffMemberResponse])
async def list_department_staff(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    organization_id: UUID = Depends(get_organization_id),
):
    """
    Fetch all staff members for the current organization/department.
    Powers the 'Roles & Permissions' data table.
    """
    if current_user.role not in ["admin", "doctor", "hospital"]:
        raise HTTPException(status_code=403, detail="Access denied")

    # Fetch users in this organization
    query = select(User).where(
        User.organization_id == organization_id, 
        User.deleted_at.is_(None)
    ).order_by(User.full_name.asc())
    
    result = await db.execute(query)
    users = result.scalars().all()

    staff_list = []
    for u in users:
        # Decrypt name if needed
        try:
            name = pii_encryption.decrypt(u.full_name)
        except:
            name = u.full_name if u.full_name else "Encrypted/Unknown"
            
        staff_list.append(StaffMemberResponse(
            id=u.id,
            name=name,
            email=u.email,
            # Fallback to system role if specific department_role is empty
            role=getattr(u, 'department_role', None) or u.role.capitalize(),
            last_accessed=u.last_login,
            # Fallback to 'Active' if staff_status is empty
            status=getattr(u, 'staff_status', None) or "Active"
        ))

    return staff_list

@router.get("/invites/pending", response_model=list[PendingInviteResponse])
async def list_pending_invites(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    organization_id: UUID = Depends(get_organization_id),
):
    """
    Fetch all pending invitations for the current organization.
    Powers the 'Pending Invites' side-panel.
    """
    if current_user.role not in ["admin", "hospital"]:
        raise HTTPException(status_code=403, detail="Only admins can view pending invites")

    query = select(Invitation).where(
        Invitation.organization_id == organization_id,
        Invitation.status == "pending"
    ).order_by(Invitation.created_at.desc())
    
    result = await db.execute(query)
    invites = result.scalars().all()

    response_list = []
    for invite in invites:
        response_list.append(PendingInviteResponse(
            id=invite.id,
            email=invite.email,
            # Use the newly migrated department_role if available, else system role
            role=getattr(invite, 'department_role', None) or invite.role.capitalize(),
            expires_at=invite.expires_at,
            status=invite.status
        ))

    return response_list