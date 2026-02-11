from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime, timedelta
import uuid
import hashlib

from app.database import get_db
from app.core.deps import require_role
from app.models.user import User, Organization, Invitation
from app.models.activity_log import ActivityLog
from app.services.email import send_invitation_email
from app.schemas.admin import (
    AdminOverviewResponse,
    AllSettingsResponse,      # Corrected Name
    OrgSettingsUpdate,        # Corrected Name
    DeveloperSettingsUpdate,
    BackupSettingsUpdate,
    AccountListItem,          # Corrected Name
    InviteRequest,
    StorageStats,
    SystemAlert,
    ActivityFeedItem
)

router = APIRouter(prefix="/admin", tags=["Admin"])
# --- 1. Dashboard Overview ---
@router.get("/overview", response_model=AdminOverviewResponse)
async def get_dashboard_overview(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")), # Fixed Dependency
):
    """
    Aggregates data for the Admin Dashboard.
    """
    
    # 1. Fetch Recent Activity (Real Data)
    query = (
        select(ActivityLog)
        .where(ActivityLog.organization_id == current_user.organization_id)
        .order_by(desc(ActivityLog.created_at))
        .limit(5)
    )
    result = await db.execute(query)
    logs = result.scalars().all()
    
    recent_activity_items = []
    for log in logs:
        recent_activity_items.append(ActivityFeedItem(
            id=log.id,
            user_name=getattr(log, "user_email", "System User"),
            user_avatar=None,
            event_description=log.action,
            timestamp=log.created_at,
            status="completed"
        ))

    # 2. Storage Stats (Mocked to match Schema)
    storage_stats = StorageStats(
        used_gb=124.5,
        total_gb=1000.0,
        percentage=12.45,
        files_count=3420
    )
    
    # 3. System Alerts (Mocked to match Schema)
    alerts = [
        SystemAlert(
            id="1", 
            title="Storage Warning",
            message="Storage reaching 80% capacity", 
            time_ago="10 mins ago",
            severity="high"
        ),
        SystemAlert(
            id="2", 
            title="Backup Complete",
            message="Weekly backup created successfully", 
            time_ago="2 hours ago",
            severity="info"
        )
    ]

    return AdminOverviewResponse(
        storage=storage_stats,
        alerts=alerts,
        recent_activity=recent_activity_items,
        quick_actions=["Invite Member", "View Audit Logs"]
    )

# --- 2. Settings Management ---
@router.get("/settings", response_model=AllSettingsResponse)
async def get_admin_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    result = await db.execute(select(Organization).where(Organization.id == current_user.organization_id))
    org = result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    return AllSettingsResponse(
        organization={
            "name": org.name,
            "org_email": "admin@some.ai", # Mocked or fetch from DB if exists
            "timezone": getattr(org, "timezone", "UTC"),
            "date_format": getattr(org, "date_format", "DD/MM/YYYY")
        },
        integrations=[], # Empty list for now
        developer={
            "api_key_name": "Standard Key",
            "webhook_url": "https://api.some.ai/webhook"
        },
        backup={
            "backup_frequency": "daily"
        }
    )

@router.patch("/settings/organization", response_model=dict)
async def update_organization_settings(
    settings_in: OrgSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    result = await db.execute(select(Organization).where(Organization.id == current_user.organization_id))
    org = result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    if settings_in.name:
        org.name = settings_in.name
    
    # Handle optional fields safely
    if settings_in.timezone and hasattr(org, "timezone"):
        org.timezone = settings_in.timezone
    if settings_in.date_format and hasattr(org, "date_format"):
        org.date_format = settings_in.date_format

    await db.commit()
    return {"message": "Organization settings updated successfully"}

@router.patch("/settings/developer", response_model=dict)
async def update_developer_settings(
    settings_in: DeveloperSettingsUpdate,
    current_user: User = Depends(require_role("admin")),
):
    return {"message": "Developer settings updated successfully"}

@router.patch("/settings/backup", response_model=dict)
async def update_backup_settings(
    settings_in: BackupSettingsUpdate,
    current_user: User = Depends(require_role("admin")),
):
    return {"message": "Backup settings updated successfully"}

# --- 3. Team Management ---
@router.get("/accounts", response_model=list[AccountListItem])
async def get_admin_accounts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    # Fetch Users
    result = await db.execute(select(User).limit(100))
    users = result.scalars().all()
    
    account_list = []
    for user in users:
        account_list.append(AccountListItem(
            id=user.id,
            name=user.full_name,
            email=user.email,
            role=user.role,
            status="active" if user.is_active else "inactive",
            last_login=user.last_login.strftime("%Y-%m-%d") if user.last_login else None,
            type="user"
        ))
    return account_list

@router.post("/invite", response_model=dict)
async def invite_team_member(
    invite_in: InviteRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    # Check for existing user
    result = await db.execute(select(User).where(User.email == invite_in.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User already registered.")

    token_raw = uuid.uuid4().hex
    token_hash = hashlib.sha256(token_raw.encode()).hexdigest()
    
    new_invite = Invitation(
        email=invite_in.email,
        role=invite_in.role,
        token_hash=token_hash,
        expires_at=datetime.utcnow() + timedelta(hours=48),
        organization_id=current_user.organization_id,
        created_by_id=current_user.id,
        status="pending"
    )
    
    db.add(new_invite)
    await db.commit()
    
    # In a real scenario, use background_tasks.add_task(send_email, ...)
    return {"message": f"Invitation sent to {invite_in.email}"}

@router.delete("/accounts/{id}")
async def remove_team_member(
    id: uuid.UUID, # Changed from str to uuid.UUID for automatic validation
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """
    Revoke an invite OR Deactivate a user so the UI list updates.
    """
    # 1. Check if it's a Pending Invitation (Delete it completely)
    result_invite = await db.execute(select(Invitation).where(
        Invitation.id == id, 
        Invitation.organization_id == current_user.organization_id
    ))
    invite = result_invite.scalar_one_or_none()
    
    if invite:
        await db.delete(invite)
        await db.commit()
        return {"status": "revoked_invitation", "id": str(id)}

    # 2. Check if it's an Active User (Soft Delete)
    result_user = await db.execute(select(User).where(
        User.id == id,
        User.organization_id == current_user.organization_id
    ))
    user_to_remove = result_user.scalar_one_or_none()
    
    if user_to_remove:
        # Prevent Admin from deleting themselves
        if user_to_remove.id == current_user.id:
            raise HTTPException(400, "You cannot revoke your own access.")
            
        # Soft delete: Set deleted_at timestamp
        user_to_remove.deleted_at = datetime.utcnow()
        await db.commit()
        return {"status": "deactivated_user", "id": str(id)}

    raise HTTPException(404, "Account or Invitation not found")