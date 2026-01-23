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
from app.schemas.team import TeamInviteCreate, TeamRole

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
