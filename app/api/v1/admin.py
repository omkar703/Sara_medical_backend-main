import os
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from app.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, case
from datetime import datetime, timedelta, time, timezone
import uuid
from app.services.minio_service import minio_service
from sqlalchemy.orm import selectinload
from typing import List
import hashlib

from app.database import get_db
from app.core.deps import require_role
from app.models.user import User, Organization, Invitation
from app.models.activity_log import ActivityLog
from app.models.appointment import Appointment
from app.services.email import send_invitation_email
from app.schemas.admin import (
    AdminOverviewResponse,
    AllSettingsResponse,
    OrgSettingsUpdate,
    DeveloperSettingsUpdate,
    BackupSettingsUpdate,
    AccountListItem,
    InviteRequest,
    StorageStats,
    SystemAlert,
    ActivityFeedItem,
    AdminDoctorDetailResponse,
    AdminInvitationItem,         # NEW
    AdminOrgAppointmentItem,      # NEW
    AdminAccountUpdate,
    AdminGlobalAppointmentItem,
    AdminClinicStatsItem,
    AdminProfileSchema,
    AdminProfileUpdate
)

router = APIRouter(prefix="/admin", tags=["Admin"])

# --- 1. Dashboard Overview (UPDATED) ---
@router.get("/overview", response_model=AdminOverviewResponse)
async def get_dashboard_overview(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """
    Aggregates data for the Admin Dashboard globally.
    """
    from sqlalchemy.orm import selectinload
    
    # 1. Fetch Recent Activity 
    query = (
        select(ActivityLog)
        .options(selectinload(ActivityLog.user))
        .where(ActivityLog.organization_id == current_user.organization_id)
        .order_by(desc(ActivityLog.created_at))
        .limit(5)
    )
    result = await db.execute(query)
    logs = result.scalars().all()
    
    try:
        from app.core.security import pii_encryption
    except ImportError:
        pii_encryption = None
        
    recent_activity_items = []
    for log in logs:
        display_name = "System Activity"
        if log.user:
            encrypted_val = log.user.full_name or log.user.email
            if encrypted_val:
                if pii_encryption:
                    try:
                        display_name = pii_encryption.decrypt(encrypted_val)
                    except Exception:
                        display_name = "Unknown User"
                else:
                    display_name = encrypted_val
                
        recent_activity_items.append(ActivityFeedItem(
            id=log.id,
            user_name=display_name,
            user_avatar=None,
            event_description=log.activity_type or "System Event",
            timestamp=log.created_at,
            status=log.status or "completed"
        ))

    # 2. Storage Stats (Mocked)
    storage_stats = StorageStats(used_gb=124.5, total_gb=1000.0, percentage=12.45, files_count=3420)
    
    # 3. System Alerts (Mocked)
    alerts = [
        SystemAlert(id="1", title="Storage Warning", message="Storage reaching 80%", time_ago="10 mins ago", severity="high")
    ]

    # 4. NEW: Global Total Doctors
    doctor_count_query = select(func.count(User.id)).where(User.role == "doctor", User.deleted_at.is_(None))
    doctor_count_result = await db.execute(doctor_count_query)
    total_doctors = doctor_count_result.scalar_one_or_none() or 0

    # 5. NEW: Global Appointments Today
    now_utc = datetime.now(timezone.utc)
    today_start = datetime.combine(now_utc.date(), time.min).replace(tzinfo=timezone.utc)
    today_end = datetime.combine(now_utc.date(), time.max).replace(tzinfo=timezone.utc)
    
    appt_count_query = select(func.count(Appointment.id)).where(
        Appointment.requested_date >= today_start,
        Appointment.requested_date <= today_end
    )
    appt_count_result = await db.execute(appt_count_query)
    appointments_today = appt_count_result.scalar_one_or_none() or 0

    return AdminOverviewResponse(
        storage=storage_stats,
        alerts=alerts,
        recent_activity=recent_activity_items,
        quick_actions=["Invite Member", "View Audit Logs"],
        appointments_today=appointments_today,
        total_doctors=total_doctors
    )

# --- 2. Global Invitations List (NEW) ---
@router.get("/invitations", response_model=list[AdminInvitationItem])
async def get_all_invitations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """
    Fetch all user invitations globally across all organizations.
    """
    query = select(Invitation).order_by(desc(Invitation.created_at))
    result = await db.execute(query)
    invitations = result.scalars().all()
    
    return [
        AdminInvitationItem(
            id=inv.id,
            email=inv.email,
            role=inv.role,
            status=inv.status,
            organization_id=inv.organization_id,
            expires_at=inv.expires_at,
            created_at=inv.created_at
        ) for inv in invitations
    ]

# --- 3. Organization Specific Appointments (NEW) ---
@router.get("/organizations/{org_id}/appointments", response_model=list[AdminOrgAppointmentItem])
async def get_org_appointments(
    org_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """
    Fetch all appointments belonging to doctors in a specific organization.
    """
    from sqlalchemy.orm import selectinload
    try:
        from app.core.security import pii_encryption
    except ImportError:
        pii_encryption = None
    
    # Join Appointment with Doctor (User) to filter by organization_id
    query = (
        select(Appointment)
        .join(User, Appointment.doctor_id == User.id)
        .options(selectinload(Appointment.doctor), selectinload(Appointment.patient))
        .where(User.organization_id == org_id)
        .order_by(desc(Appointment.requested_date))
    )
    result = await db.execute(query)
    appointments = result.scalars().all()
    
    response_list = []
    for appt in appointments:
        doc_name = "Unknown Doctor"
        if appt.doctor:
            try:
                doc_name = pii_encryption.decrypt(appt.doctor.full_name) if pii_encryption else appt.doctor.full_name
            except Exception:
                pass
                
        pat_name = "Unknown Patient"
        if appt.patient:
            try:
                pat_name = pii_encryption.decrypt(appt.patient.full_name) if pii_encryption else appt.patient.full_name
            except Exception:
                pass
        
        response_list.append(AdminOrgAppointmentItem(
            id=appt.id,
            doctor_id=appt.doctor_id,
            patient_id=appt.patient_id,
            requested_date=appt.requested_date,
            reason=appt.reason,
            status=appt.status,
            doctor_name=doc_name,
            patient_name=pat_name,
            created_at=appt.created_at
        ))
        
    return response_list

@router.get("/accounts", response_model=list[AccountListItem])
async def get_admin_accounts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """
    Dumps all user accounts across ALL organizations.
    """
    from sqlalchemy.orm import selectinload
    
    # Query all users and eagerly load their organization relationship
    result = await db.execute(select(User).options(selectinload(User.organization)))
    users = result.scalars().all()
    
    try:
        from app.core.security import pii_encryption
    except ImportError:
        pii_encryption = None
        
    account_list = []
    for user in users:
        # Decrypt PII data
        full_name = user.full_name
        email = user.email
        if pii_encryption:
            try:
                if full_name: full_name = pii_encryption.decrypt(full_name)
            except Exception: pass
            
        account_list.append(AccountListItem(
            id=user.id,
            name=full_name or "Unknown User",
            email=email or "No Email",
            role=user.role,
            status="active" if user.deleted_at is None else "inactive",
            last_login=user.last_login.strftime("%Y-%m-%d") if user.last_login else None,
            type="user",
            organization_id=user.organization_id,
            organization_name=user.organization.name if user.organization else "Unknown Clinic"
        ))
    return account_list

# --- 2. Edit an Account (NEW) ---
@router.patch("/accounts/{id}")
async def update_admin_account(
    id: uuid.UUID,
    update_data: AdminAccountUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """
    Edit basic account information. Handles PII encryption automatically.
    """
    result = await db.execute(select(User).where(User.id == id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    try:
        from app.core.security import pii_encryption
    except ImportError:
        pii_encryption = None
        
    # 1. Update Name (Requires Encryption)
    if update_data.name:
        user.full_name = pii_encryption.encrypt(update_data.name) if pii_encryption else update_data.name
        
    # 2. Update Email
    if update_data.email:
        # Check for duplicates before updating
        conflict_check = await db.execute(select(User).where(User.email == update_data.email, User.id != id))
        if conflict_check.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email is already in use by another account.")
        user.email = update_data.email
        
    # 3. Update Role
    if update_data.role:
        user.role = update_data.role
        
    # 4. Update Status (Soft Delete / Reactivate)
    if update_data.status:
        status_lower = update_data.status.lower()
        if status_lower == "inactive":
            if user.id == current_user.id:
                raise HTTPException(status_code=400, detail="You cannot deactivate your own admin account.")
            if user.deleted_at is None:
                user.deleted_at = datetime.utcnow()
        elif status_lower == "active":
            user.deleted_at = None
            
    user.updated_at = datetime.utcnow()
    await db.commit()
    
    return {"message": "Account updated successfully"}

# --- 3. Delete an Account (Global Update) ---
@router.delete("/accounts/{id}")
async def remove_team_member(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """
    Revoke an invite OR Deactivate a user globally.
    """
    # 1. Check if it's a Pending Invitation (Delete it completely)
    # Removed the organization_id filter so admin can delete any invitation globally
    result_invite = await db.execute(select(Invitation).where(Invitation.id == id))
    invite = result_invite.scalar_one_or_none()
    
    if invite:
        await db.delete(invite)
        await db.commit()
        return {"status": "revoked_invitation", "id": str(id)}

    # 2. Check if it's an Active User (Soft Delete)
    # Removed the organization_id filter so admin can soft-delete any user globally
    result_user = await db.execute(select(User).where(User.id == id))
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

@router.get("/organizations/stats", response_model=List[AdminClinicStatsItem])
async def get_clinic_management_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """
    Fetch active staff counts and total patient counts for every organization.
    Active staff includes non-deleted users with doctor, admin, or hospital roles.
    """
    # Use conditional aggregation to count roles per organization efficiently
    query = (
        select(
            Organization.id.label("organization_id"),
            Organization.name.label("organization_name"),
            func.count(
                case(
                    (
                        (User.role.in_(["doctor", "admin", "hospital"])) & 
                        (User.deleted_at.is_(None)), 
                        User.id
                    )
                )
            ).label("active_staff_count"),
            func.count(
                case(
                    (
                        User.role == "patient", 
                        User.id
                    )
                )
            ).label("total_patient_count")
        )
        .outerjoin(User, Organization.id == User.organization_id)
        .group_by(Organization.id, Organization.name)
        .order_by(Organization.name)
    )
    
    result = await db.execute(query)
    stats_rows = result.all()
    
    # Convert SQLAlchemy Row objects to the Pydantic schema
    return [
        AdminClinicStatsItem(
            organization_id=row.organization_id,
            organization_name=row.organization_name,
            active_staff_count=row.active_staff_count,
            total_patient_count=row.total_patient_count
        ) for row in stats_rows
    ]

@router.get("/appointments/all", response_model=List[AdminGlobalAppointmentItem])
async def get_all_appointments_dump(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """
    Fetch every appointment in the system across all organizations.
    Includes decrypted doctor/patient names and organization context.
    """
    # 1. Query all appointments with related data
    # We load the doctor (and their organization) and the patient
    query = (
        select(Appointment)
        .options(
            selectinload(Appointment.doctor).selectinload(User.organization),
            selectinload(Appointment.patient)
        )
        .order_by(desc(Appointment.requested_date))
    )
    result = await db.execute(query)
    appointments = result.scalars().all()

    try:
        from app.core.security import pii_encryption
    except ImportError:
        pii_encryption = None

    response_list = []
    for appt in appointments:
        # 2. Decrypt Doctor Name
        doctor_display = "Unknown Doctor"
        org_display = "Unknown Organization"
        if appt.doctor:
            if pii_encryption and appt.doctor.full_name:
                try:
                    doctor_display = pii_encryption.decrypt(appt.doctor.full_name)
                except Exception:
                    doctor_display = appt.doctor.full_name
            else:
                doctor_display = appt.doctor.full_name or "Unknown Doctor"
            
            if appt.doctor.organization:
                org_display = appt.doctor.organization.name

        # 3. Decrypt Patient Name
        patient_display = "Unknown Patient"
        if appt.patient:
            if pii_encryption and appt.patient.full_name:
                try:
                    patient_display = pii_encryption.decrypt(appt.patient.full_name)
                except Exception:
                    patient_display = appt.patient.full_name
            else:
                patient_display = appt.patient.full_name or "Unknown Patient"

        # 4. Map to Schema
        response_list.append(AdminGlobalAppointmentItem(
            id=appt.id,
            requested_date=appt.requested_date,
            status=appt.status,
            reason=appt.reason,
            doctor_name=doctor_display,
            patient_name=patient_display,
            organization_name=org_display,
            created_at=appt.created_at
        ))

    return response_list

# --- 2. Settings Management ---
@router.get("/settings", response_model=AllSettingsResponse)
async def get_admin_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    # 1. Fetch Organization Info
    result = await db.execute(select(Organization).where(Organization.id == current_user.organization_id))
    org = result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # 2. Prepare Profile Info (Decrypted)
    try:
        from app.core.security import pii_encryption
        display_name = pii_encryption.decrypt(current_user.full_name) if current_user.full_name else "Admin"
    except Exception:
        display_name = current_user.full_name or "Admin"

    # Generate a preview URL for the avatar if it exists
    avatar_preview = None
    if current_user.avatar_url:
        avatar_preview = minio_service.generate_presigned_url(
            bucket_name=settings.MINIO_BUCKET_AVATARS,
            object_name=current_user.avatar_url
        )

    return AllSettingsResponse(
        profile=AdminProfileSchema(
            name=display_name,
            email=current_user.email,
            avatar_url=avatar_preview
        ),
        organization={
            "name": org.name,
            "org_email": "admin@clinic.ai",
            "timezone": getattr(org, "timezone", "UTC"),
            "date_format": getattr(org, "date_format", "DD/MM/YYYY")
        },
        integrations=[],
        developer={"api_key_name": "Standard Key", "webhook_url": "https://api.clinic.ai/webhook"},
        backup={"backup_frequency": "daily"}
    )

@router.patch("/settings/profile")
async def update_admin_profile(
    profile_in: AdminProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """Update the logged-in admin's personal information"""
    try:
        from app.core.security import pii_encryption
    except ImportError:
        pii_encryption = None

    if profile_in.name:
        current_user.full_name = pii_encryption.encrypt(profile_in.name) if pii_encryption else profile_in.name
    
    if profile_in.email:
        # Check for email conflicts
        conflict = await db.execute(select(User).where(User.email == profile_in.email, User.id != current_user.id))
        if conflict.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already in use")
        current_user.email = profile_in.email

    await db.commit()
    return {"message": "Profile updated successfully"}

@router.post("/settings/avatar")
async def upload_admin_avatar(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """Upload and set the admin's profile picture"""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")

    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"admin_{current_user.id}_{uuid.uuid4().hex}{file_extension}"
    
    file_content = await file.read()
    success = minio_service.upload_bytes(
        file_data=file_content,
        bucket_name=settings.MINIO_BUCKET_AVATARS,
        object_name=unique_filename,
        content_type=file.content_type
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to upload to storage")
        
    current_user.avatar_url = unique_filename
    await db.commit()

    preview_url = minio_service.generate_presigned_url(
        bucket_name=settings.MINIO_BUCKET_AVATARS,
        object_name=unique_filename
    )
    
    return {"message": "Avatar updated", "preview_url": preview_url}

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
    
    try:
        from app.core.security import pii_encryption
    except ImportError:
        pii_encryption = None
        
    account_list = []
    for user in users:
        # Decrypt PII data
        full_name = user.full_name
        email = user.email
        if pii_encryption:
            try:
                if full_name: full_name = pii_encryption.decrypt(full_name)
            except Exception: pass
            try:
                if email: email = pii_encryption.decrypt(email)
            except Exception: pass
            
        account_list.append(AccountListItem(
            id=user.id,
            name=full_name or "Unknown User",
            email=email or "No Email",
            role=user.role,
            status="active" if user.deleted_at is None else "inactive",
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
    from app.models.user import Organization
    result = await db.execute(select(Organization).where(Organization.id == current_user.organization_id))
    org = result.scalar_one_or_none()
    org_name = org.name if org else "Saramedico"

    # Add the task to send the email in the background
    background_tasks.add_task(
        send_invitation_email,
        email=invite_in.email,
        token=token_raw, # Use the raw UUID hex, not the hash
        role=invite_in.role,
        org_name=org_name
    )
    
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

        return {"status": "deactivated_user", "id": str(id)}

    raise HTTPException(404, "Account or Invitation not found")

@router.get("/doctors/{doctor_id}/details", response_model=AdminDoctorDetailResponse)
async def get_admin_doctor_details(
    doctor_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """
    Fetch comprehensive profile data, stats, upcoming appointments, 
    and recent patients for a specific doctor.
    """
    from app.core.security import pii_encryption
    from app.models.appointment import Appointment
    from app.schemas.admin import AdminDoctorDetailResponse, DoctorStats, DoctorApptItem, DoctorPatientItem
    from sqlalchemy.orm import selectinload

    # 1. Fetch Doctor
    result = await db.execute(select(User).where(User.id == doctor_id, User.role == "doctor"))
    doctor = result.scalar_one_or_none()
    
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
        
    full_name_decrypted = "Unknown"
    email_decrypted = "No Email"
    try:
        full_name_decrypted = pii_encryption.decrypt(doctor.full_name) if doctor.full_name else "Unknown"
        email_decrypted = pii_encryption.decrypt(doctor.email) if doctor.email else "No Email"
    except Exception:
        pass
        
    first_name = full_name_decrypted.split(" ")[0]
    last_name = " ".join(full_name_decrypted.split(" ")[1:]) if " " in full_name_decrypted else ""

    # 2. Fetch Appointments & Compute Stats
    # For stats, we count total distinct patients and total appointments.
    appt_result = await db.execute(
        select(Appointment)
        .options(selectinload(Appointment.patient))
        .where(Appointment.doctor_id == doctor_id)
        .order_by(Appointment.requested_date.desc())
    )
    all_appts = appt_result.scalars().all()
    
    total_consultations = len(all_appts)
    patient_ids = set()
    upcoming_appts = []
    recent_patients = []
    
    from datetime import timezone
    now = datetime.now(timezone.utc)
    
    patient_map = {} # patient_id -> Patient model

    for appt in all_appts:
        patient_ids.add(appt.patient_id)
        if appt.patient:
            patient_map[appt.patient_id] = appt.patient
            
        # Upcoming
        # Ensure comparable datetimes by making requested_date aware if it isn't, 
        # or replacing tzinfo for naive comparison
        req_date = appt.requested_date
        if req_date.tzinfo is None:
            req_date = req_date.replace(tzinfo=timezone.utc)

        if req_date > now and len(upcoming_appts) < 5:
            pat_name = "Unknown Patient"
            if appt.patient:
                try: pat_name = pii_encryption.decrypt(appt.patient.full_name)
                except: pass
                
            upcoming_appts.append(DoctorApptItem(
                id=appt.id,
                patientName=pat_name,
                time=appt.requested_date.strftime("%b %d, %Y %I:%M %p"),
                status=appt.status.capitalize()
            ))

    # Derive recent patients from the 5 most recent appointments
    for pat_id, pat_obj in list(patient_map.items())[:5]:
        pat_name = "Unknown Patient"
        try: pat_name = pii_encryption.decrypt(pat_obj.full_name)
        except: pass
        
        recent_patients.append(DoctorPatientItem(
            id=pat_obj.id,
            name=pat_name,
            condition="Unknown Condition", # Real condition from medical history if available later
            lastVisit="Recently" # Derive from latest appointment if needed
        ))

    stats = DoctorStats(
        totalPatients=len(patient_ids),
        consultations=total_consultations,
        rating=4.9 # Mocked until feedback system exists
    )

    return AdminDoctorDetailResponse(
        id=doctor.id,
        first_name=first_name,
        last_name=last_name,
        email=email_decrypted,
        specialty=doctor.specialty or "General Practice",
        status="active" if doctor.deleted_at is None else "inactive",
        phone=None,
        license=None,
        joinedDate=doctor.created_at.strftime("%b %d, %Y") if doctor.created_at else "Unknown",
        stats=stats,
        appointments=upcoming_appts,
        patients=recent_patients
    )

@router.get("/audit-logs")
async def get_audit_logs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """
    Fetch the last 50 activity logs for the admin's organization.
    """
    from sqlalchemy.orm import selectinload
    
    query = (
        select(ActivityLog)
        .options(selectinload(ActivityLog.user))
        .where(ActivityLog.organization_id == current_user.organization_id)
        .order_by(desc(ActivityLog.created_at))
        .limit(50)
    )
    result = await db.execute(query)
    logs = result.scalars().all()
    
    try:
        from app.core.security import pii_encryption
    except ImportError:
        pii_encryption = None
        
    formatted_logs = []
    for log in logs:
        display_name = "System Activity"
        if log.user:
            encrypted_val = log.user.full_name or log.user.email
            if encrypted_val:
                if pii_encryption:
                    try:
                        display_name = pii_encryption.decrypt(encrypted_val)
                    except Exception:
                        display_name = "Unknown User"
                else:
                    display_name = encrypted_val
                    
        formatted_logs.append({
            "id": str(log.id),
            "action": log.activity_type or "System Event",
            "user": display_name,
            "timestamp": log.created_at.isoformat() if log.created_at else None
        })

    return {"logs": formatted_logs}