from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime

import uuid
import hashlib
from datetime import timedelta

from app.database import get_db
from app.core.deps import require_role
from app.models.user import User, Organization, Invitation 
from app.models.activity_log import ActivityLog
from app.services.email import send_invitation_email
from app.schemas.admin import (
    AdminOverviewResponse, 
    ActivityFeedItem, 
    SystemAlert,
    StorageStats,
    AllSettingsResponse,
    OrgSettingsUpdate,
    AccountListItem, InviteRequest
)

router = APIRouter(prefix="/admin", tags=["Admin Console"])

# --- 1. Dashboard Overview ---
@router.get("/overview", response_model=AdminOverviewResponse)
async def get_dashboard_overview(
    current_user: User = Depends(require_role("admin")), 
    db: AsyncSession = Depends(get_db)
):

    org_result = await db.execute(
        select(Organization).where(Organization.id == current_user.organization_id)
    )
    org = org_result.scalar_one()

    query = (
        select(ActivityLog)
        .where(ActivityLog.organization_id == current_user.organization_id)
        .order_by(desc(ActivityLog.created_at))
        .limit(5)
    )
    result = await db.execute(query)
    logs = result.scalars().all()
    
    activity_items = []
    for log in logs:

        activity_items.append(ActivityFeedItem(
            id=log.id,
            user_name="System User", 
            user_avatar=None,
            event_description=log.activity_type,
            timestamp=log.created_at,
            status=log.status or "Completed"
        ))

    # Mock Alerts
    alerts = [
        SystemAlert(
            id="1", title="Consultation summary ready", 
            message="Patient Daniel Koshear - AI Analysis complete.", 
            time_ago="42m ago", severity="info"
        )
    ]

    # Mock Storage 
    storage = StorageStats(
        used_gb=120,    # Mocked
        total_gb=500,   # Mocked
        percent_used=24.0
    )

    return AdminOverviewResponse(
        recent_activity=activity_items,
        alerts=alerts,
        storage=storage,
        quick_actions=["invite_user", "view_reports"]
    )

# --- 2. Settings ---

@router.get("/settings", response_model=AllSettingsResponse)
async def get_all_settings(
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):

    org_result = await db.execute(
        select(Organization).where(Organization.id == current_user.organization_id)
    )
    org = org_result.scalar_one()
    
    return AllSettingsResponse(
        organization={
            "name": org.name,
            "email": "admin@saramedico.com", # Mocked
            "timezone": "UTC-5 (EST)", # Mocked
            "date_format": "MM/DD/YYYY" # Mocked
        },
        integrations=[
            {"name": "EPIC Systems", "status": "Connected", "last_sync": "2 mins ago"},
        ],
        developer={
            "api_key_name": "Production Server 01", # Mocked
            "webhook_url": "https://api.saramedico.com/webhooks" # Mocked
        },
        backup={
            "frequency": "Daily", # Mocked
            "last_backup": datetime.utcnow() # Mocked
        }
    )

@router.patch("/settings/organization")
async def update_org_settings(
    data: OrgSettingsUpdate,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):

    org_result = await db.execute(
        select(Organization).where(Organization.id == current_user.organization_id)
    )
    org = org_result.scalar_one()
    

    if data.name:
        org.name = data.name
        
    await db.commit()
    return {"status": "updated", "note": "Only name was persisted"}

@router.get("/accounts", response_model=list[AccountListItem])
async def get_account_list(
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Provides a lits of active accounts and pending iniviation accounts.
    """
    org_id = current_user.organization_id
    

    users_query = select(User).where(User.organization_id == org_id)
    users_result = await db.execute(users_query)
    users = users_result.scalars().all()
    

    invites_query = select(Invitation).where(
        Invitation.organization_id == org_id,
        Invitation.status == "pending"
    )
    invites_result = await db.execute(invites_query)
    invites = invites_result.scalars().all()
    
    accounts = []
    

    for u in users:

        status = "Active"
        if u.deleted_at: status = "Inactive"
        
        accounts.append(AccountListItem(
            id=u.id,
            name=u.full_name,
            email=u.email,
            role=u.role.title(),
            status=status,
            last_login=u.last_login.strftime("%m/%d/%y") if u.last_login else "Never",
            avatar_url=u.avatar_url,
            type="user"
        ))
        

    for i in invites:
        accounts.append(AccountListItem(
            id=i.id,
            name=i.email, 
            email=i.email,
            role=i.role.title(),
            status="Pending",
            last_login="Waiting...",
            avatar_url=None,
            type="invitation"
        ))
        
    return accounts

@router.post("/invite")
async def invite_team_member(
    data: InviteRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Handles 'Invite Team Members' Form.
    Sends an email in the background.
    """
    org_id = current_user.organization_id
    

    existing_user = await db.execute(select(User).where(User.email == data.email))
    if existing_user.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User already registered.")

    existing_invite = await db.execute(select(Invitation).where(
        Invitation.email == data.email,
        Invitation.organization_id == org_id,
        Invitation.status == "pending"
    ))
    if existing_invite.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Invitation already pending.")


    token_raw = uuid.uuid4().hex
    token_hash = hashlib.sha256(token_raw.encode()).hexdigest()
    
    role_map = {"Administrator": "admin", "Member": "doctor", "Patient": "patient"}
    db_role = role_map.get(data.role, "doctor")

    new_invite = Invitation(
        email=data.email,
        role=db_role,
        token_hash=token_hash,
        expires_at=datetime.utcnow() + timedelta(hours=48),
        organization_id=org_id,
        created_by_id=current_user.id,
        status="pending"
    )
    
    db.add(new_invite)
    await db.commit()
    
    
    org_result = await db.execute(
        select(Organization).where(Organization.id == org_id)
    )
    org = org_result.scalar_one()
    org_name = org.name

    
    # Trigger Email in Background
    background_tasks.add_task(
        send_invitation_email, 
        email=data.email, 
        token=token_raw,
        role=data.role, 
        org_name=org_name
    )
    
    return {"status": "invited", "email": data.email}

@router.delete("/accounts/{id}")
async def revoke_access(
    id: uuid.UUID,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Revoke an invite OR Deactivate a user.
    """
    result_invite = await db.execute(select(Invitation).where(
        Invitation.id == id, 
        Invitation.organization_id == current_user.organization_id
    ))
    invite = result_invite.scalar_one_or_none()
    
    if invite:
        await db.delete(invite)
        await db.commit()
        return {"status": "revoked_invitation"}

    result_user = await db.execute(select(User).where(
        User.id == id,
        User.organization_id == current_user.organization_id
    ))
    user_to_remove = result_user.scalar_one_or_none()
    
    if user_to_remove:
        if user_to_remove.id == current_user.id:
            raise HTTPException(400, "You cannot revoke your own access.")
            

        user_to_remove.deleted_at = datetime.utcnow()
        await db.commit()
        return {"status": "deactivated_user"}


    raise HTTPException(404, "Account or Invitation not found")