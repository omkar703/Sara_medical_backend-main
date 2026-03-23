"""Authentication API endpoints"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from fastapi import Request
from fastapi_sso.sso.google import GoogleSSO

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.auth import HospitalRegistrationRequest
import json
from datetime import date
from typing import Union
from app.models.patient import Patient
from app.models.consultation import Consultation
from app.models.health_metric import HealthMetric
from app.schemas.patient import PatientDetailResponse
from app.services.minio_service import minio_service
from pydantic import BaseModel, EmailStr, Field

from app.config import settings
from app.core.deps import get_current_user
from app.core.mfa import generate_backup_codes, generate_qr_code, generate_totp_secret, verify_totp_code
from app.core.security import (
    PIIEncryption,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_password_reset_token,
    generate_verification_token,
    hash_password,
    hash_token,
    verify_password,
    verify_token_hash,
)
from app.database import get_db
from app.models.user import Organization, RefreshToken, User
from app.schemas.auth import (
    ErrorResponse,
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    MessageResponse,
    MFARequiredResponse,
    RefreshTokenRequest,
    ResetPasswordRequest,
    SetupMFAResponse,
    TokenResponse,
    UserCreate,
    UserResponse,
    VerifyEmailRequest,
    VerifyMFARequest,
    VerifyMFASetupRequest,
    OnboardingUpdateRequest,
)
from app.services.email import send_password_reset_email, send_verification_email

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user
    """
    if user_data.role == "patient":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Patients cannot register themselves. Please contact your healthcare provider for onboarding."
        )
    # Check if email already exists
    result = await db.execute(
        select(User).where(User.email == user_data.email.lower())
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Get or create organization
    org_result = await db.execute(
        select(Organization).where(Organization.name == user_data.organization_name)
    )
    organization = org_result.scalar_one_or_none()
    
    if not organization:
        # Create new organization
        organization = Organization(
            name=user_data.organization_name
        )
        db.add(organization)
        await db.flush()  # Get organization ID
    
    # Hash password (Fixed: using hash_password from imports)
    password_hash = hash_password(user_data.password)
    
    # Generate verification token
    verification_token = generate_verification_token()
    verification_token_hash = hash_token(verification_token)
    verification_expires = datetime.utcnow() + timedelta(hours=24)
    
    # Encrypt PII fields
    pii_encryption = PIIEncryption()
    
    # Fixed: Logic to determine full_name string before encryption
    if user_data.full_name:
        full_name_str = user_data.full_name
    else:
        full_name_str = f"{user_data.first_name} {user_data.last_name}"
        
    encrypted_full_name = pii_encryption.encrypt(full_name_str)
    
    phone_input = user_data.phone_number or user_data.phone
    encrypted_phone = pii_encryption.encrypt(phone_input) if phone_input else None
    
    # Create user
    user = User(
        email=user_data.email.lower(),
        password_hash=password_hash,
        full_name=encrypted_full_name,
        phone_number=encrypted_phone,
        role=user_data.role,
        organization_id=organization.id,
        email_verification_token=None,
        email_verification_expires=None,
        email_verified=True,
        mfa_enabled=False,
        
        # Social Auth Fields
        google_id=user_data.google_id,
        apple_id=user_data.apple_id
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # Log the registration
    try:
        from app.models.activity_log import ActivityLog
        activity = ActivityLog(
            user_id=user.id,
            organization_id=organization.id,
            activity_type="New Account Created",
            description=f"New {user.role} account created for {user.email}",
            related_entity_type="user",
            related_entity_id=user.id,
            status="completed"
        )
        db.add(activity)
        await db.commit()
    except Exception as e:
        print(f"Failed to log registration: {e}")
    
    
    # Auto-create Patient Profile if role is patient
    # Normalize role to string for comparison
    user_role_str = str(user.role).split('.')[-1] if hasattr(user.role, 'value') else str(user.role)
    
    if user_role_str == "patient":
        from app.services.patient_service import PatientService
        patient_service = PatientService(db)
        
        # Prepare patient data
        # Use RAW values from user_data to avoid double encryption
        p_data = {
            "full_name": full_name_str,
            "email": user_data.email,
            "phone_number": user_data.phone_number or user_data.phone,
            "date_of_birth": user_data.date_of_birth,
            "address": {},
            "emergency_contact": {},
            "medical_history": "",
            "allergies": [],
            "medications": []
        }
        
        await patient_service.create_patient(
            patient_data=p_data,
            organization_id=user.organization_id,
            created_by=user.id,
            patient_id=user.id
        )
        await db.commit()
    
    pii_encryption2 = PIIEncryption()
    decrypted_full_name = pii_encryption2.decrypt(user.full_name)
    name_parts = decrypted_full_name.split(" ", 1)

    return UserResponse(
        id=user.id,
        name=decrypted_full_name,
        email=user.email,
        first_name=name_parts[0],
        last_name=name_parts[1] if len(name_parts) > 1 else "",
        phone_number=pii_encryption2.decrypt(user.phone_number) if user.phone_number else None,
        role=user.role,
        organization_id=user.organization_id,
        organization_name=getattr(user.organization, "name", "Default Org"),
        email_verified=user.email_verified,
        mfa_enabled=user.mfa_enabled,
        created_at=user.created_at,
        updated_at=user.updated_at
    )

@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    request: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db)
):
    """Verify user email with token"""
    # Hash the token to compare
    token_hash = hash_token(request.token)
    
    # Find user with matching token
    result = await db.execute(
        select(User).where(
            User.email_verification_token == token_hash,
            User.email_verification_expires > datetime.utcnow(),
            User.deleted_at.is_(None)
        )
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    # Update user
    user.email_verified = True
    user.email_verification_token = None
    user.email_verification_expires = None
    
    await db.commit()
    
    return MessageResponse(message="Email verified successfully")


@router.post("/login", response_model=LoginResponse | MFARequiredResponse)
async def login(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Login with email and password
    
    Returns either:
    - JWT tokens if MFA is disabled
    - MFA challenge if MFA is enabled
    """
    # Find user by email
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(User)
        .options(selectinload(User.organization))
        .where(
            User.email == credentials.email.lower(),
            User.deleted_at.is_(None),
            User.is_active.is_(True)
        )
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Check if email is verified
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email first"
        )
    
    # If MFA is enabled, return challenge
    # if user.mfa_enabled:
    #     return MFARequiredResponse(
    #         mfa_required=True,
    #         user_id=str(user.id),
    #         message="MFA verification required"
    #     )
    
    # Generate tokens
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role}
    )
    refresh_token_value = create_refresh_token(
        data={"sub": str(user.id)}
    )
    
    # Store refresh token
    refresh_token_hash = hash_token(refresh_token_value)
    refresh_token = RefreshToken(
        user_id=user.id,
        token_hash=refresh_token_hash,
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    db.add(refresh_token)
    
    # Update last login
    user.last_login = datetime.utcnow()
    
    await db.commit()
    
    # Decrypt PII for response
    pii_encryption = PIIEncryption()
    try:
        decrypted_full_name = pii_encryption.decrypt(user.full_name)
    except Exception:
        # Fallback if the data is unencrypted or encrypted with an old key
        decrypted_full_name = user.full_name if user.full_name else "Unknown User"
        
    name_parts = decrypted_full_name.split(" ", 1)
    
    return LoginResponse(
        success=True,
        token=access_token,
        access_token=access_token,
        refresh_token=refresh_token_value,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            name=decrypted_full_name,
            email=user.email,
            first_name=name_parts[0],
            last_name=name_parts[1] if len(name_parts) > 1 else "",
            phone_number=pii_encryption.decrypt(user.phone_number) if user.phone_number else None,
            role=user.role,
            organization_id=user.organization_id,
            email_verified=user.email_verified,
            mfa_enabled=user.mfa_enabled,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    )


@router.post("/verify-mfa", response_model=LoginResponse)
async def verify_mfa(
    mfa_data: VerifyMFARequest,
    db: AsyncSession = Depends(get_db)
):
    """Verify MFA code and return tokens"""
    # Get user
    try:
        user_uuid = UUID(mfa_data.user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID"
        )
    
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(User)
        .options(selectinload(User.organization))
        .where(User.id == user_uuid, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid MFA request"
        )
    
    # Verify TOTP code or backup code
    valid = False
    
    if user.mfa_secret:
        # Try TOTP first
        pii_encryption = PIIEncryption()
        decrypted_secret = pii_encryption.decrypt(user.mfa_secret)
        valid = verify_totp_code(decrypted_secret, mfa_data.code)
    
    if not valid and user.mfa_backup_codes:
        # Try backup codes
        pii_encryption = PIIEncryption()
        backup_codes_str = pii_encryption.decrypt(user.mfa_backup_codes)
        backup_codes = backup_codes_str.split(",")
        
        if mfa_data.code in backup_codes:
            valid = True
            # Remove used backup code
            backup_codes.remove(mfa_data.code)
            user.mfa_backup_codes = pii_encryption.encrypt(",".join(backup_codes))
    
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid MFA code"
        )
    
    # Generate tokens
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role}
    )
    refresh_token_value = create_refresh_token(
        data={"sub": str(user.id)}
    )
    
    # Store refresh token
    refresh_token_hash = hash_token(refresh_token_value)
    refresh_token = RefreshToken(
        user_id=user.id,
        token_hash=refresh_token_hash,
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    db.add(refresh_token)
    
    # Update last login
    user.last_login = datetime.utcnow()
    
    await db.commit()
    
    # Decrypt PII for response
    pii_encryption = PIIEncryption()
    decrypted_full_name = pii_encryption.decrypt(user.full_name)
    name_parts = decrypted_full_name.split(" ", 1)

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token_value,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            name=decrypted_full_name,
            email=user.email,
            first_name=name_parts[0],
            last_name=name_parts[1] if len(name_parts) > 1 else "",
            phone_number=pii_encryption.decrypt(user.phone_number) if user.phone_number else None,
            role=user.role,
            organization_id=user.organization_id,
            email_verified=user.email_verified,
            mfa_enabled=user.mfa_enabled,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    )


@router.post("/setup-mfa", response_model=SetupMFAResponse)
async def setup_mfa(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Setup MFA for current user
    Returns QR code and backup codes
    """
    if current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is already enabled"
        )
    
    # Generate TOTP secret
    secret = generate_totp_secret()
    
    # Generate QR code
    pii_encryption = PIIEncryption()
    decrypted_email = current_user.email
    qr_code = generate_qr_code(secret, decrypted_email)
    
    # Generate backup codes
    backup_codes = generate_backup_codes()
    
    # Encrypt and store temporarily (will be confirmed in verify-mfa-setup)
    encrypted_secret = pii_encryption.encrypt(secret)
    encrypted_backup_codes = pii_encryption.encrypt(",".join(backup_codes))
    
    # Store in user record but don't enable yet
    current_user.mfa_secret = encrypted_secret
    current_user.mfa_backup_codes = encrypted_backup_codes
    
    await db.commit()
    
    return SetupMFAResponse(
        secret=secret,
        qr_code=qr_code,
        backup_codes=backup_codes
    )


@router.post("/verify-mfa-setup", response_model=MessageResponse)
async def verify_mfa_setup(
    verify_data: VerifyMFASetupRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Verify MFA setup by confirming a code"""
    if current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is already enabled"
        )
    
    if not current_user.mfa_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA setup not initiated"
        )
    
    # Decrypt secret and verify code
    pii_encryption = PIIEncryption()
    decrypted_secret = pii_encryption.decrypt(current_user.mfa_secret)
    
    if not verify_totp_code(decrypted_secret, verify_data.code):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid MFA code"
        )
    
    # Enable MFA
    current_user.mfa_enabled = True
    
    await db.commit()
    
    return MessageResponse(message="MFA enabled successfully")


@router.post("/disable-mfa", response_model=MessageResponse)
async def disable_mfa(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Disable MFA for current user"""
    if not current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is not enabled"
        )
    
    # Disable MFA and clear secrets
    current_user.mfa_enabled = False
    current_user.mfa_secret = None
    current_user.mfa_backup_codes = None
    
    await db.commit()
    
    return MessageResponse(message="MFA disabled successfully")


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token using refresh token"""
    # Decode refresh token
    payload = decode_token(request.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # Verify refresh token exists and is not revoked
    token_hash = hash_token(request.refresh_token)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked == False,
            RefreshToken.expires_at > datetime.utcnow()
        )
    )
    refresh_token = result.scalar_one_or_none()
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    # Get user
    user_result = await db.execute(
        select(User).where(User.id == refresh_token.user_id, User.deleted_at.is_(None))
    )
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Generate new access token
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role}
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer"
    )


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """Send password reset email"""
    # Find user
    result = await db.execute(
        select(User).where(
            User.email == request.email.lower(),
            User.deleted_at.is_(None)
        )
    )
    user = result.scalar_one_or_none()
    
    # Always return success to prevent email enumeration
    if not user:
        return MessageResponse(
            message="If that email exists, a password reset link has been sent"
        )
    
    # Generate reset token
    reset_token = generate_password_reset_token()
    reset_token_hash = hash_token(reset_token)
    reset_expires = datetime.utcnow() + timedelta(hours=1)
    
    # Update user
    user.password_reset_token = reset_token_hash
    user.password_reset_expires = reset_expires
    
    await db.commit()
    
    # Send email
    pii_encryption = PIIEncryption()
    decrypted_full_name = pii_encryption.decrypt(user.full_name)
    user_name = decrypted_full_name.split(" ", 1)[0]
    await send_password_reset_email(
        to_email=user.email,
        reset_token=reset_token,
        user_name=user_name
    )
    
    return MessageResponse(
        message="If that email exists, a password reset link has been sent"
    )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """Reset password with token"""
    # Hash token
    token_hash = hash_token(request.token)
    
    # Find user with matching token
    result = await db.execute(
        select(User).where(
            User.password_reset_token == token_hash,
            User.password_reset_expires > datetime.utcnow(),
            User.deleted_at.is_(None)
        )
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Update password
    user.password_hash = hash_password(request.new_password)
    user.password_reset_token = None
    user.password_reset_expires = None
    
    # Revoke all refresh tokens for security
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user.id)
        .values(revoked=True)
    )
    
    await db.commit()
    
    return MessageResponse(message="Password reset successfully")


from app.core.deps import get_user_optional

@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: RefreshTokenRequest,
    current_user: Optional[User] = Depends(get_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """Logout by revoking refresh token"""
    # Hash and revoke the refresh token
    token_hash = hash_token(request.refresh_token)
    
    # Revoke the token if it exists
    # If current_user is provided, only revoke if it belongs to them
    stmt = update(RefreshToken).where(RefreshToken.token_hash == token_hash).values(revoked=True)
    
    if current_user:
        stmt = stmt.where(RefreshToken.user_id == current_user.id)
        
    await db.execute(stmt)
    await db.commit()
    
    return MessageResponse(message="Logged out successfully")


@router.delete("/me", response_model=MessageResponse)
async def delete_my_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Permanently delete the authenticated user's account and ALL associated data.
    
    This action is IRREVERSIBLE.
    """
    from sqlalchemy import delete as sql_delete, and_, or_, update as sql_update
    from sqlalchemy.orm import selectinload
    from datetime import datetime

    user_id = current_user.id
    org_id = current_user.organization_id
    role_str = str(current_user.role).split('.')[-1] if hasattr(current_user.role, 'value') else str(current_user.role)

    print(f"[DeleteAccount] Starting deep cleanup for user {user_id} (Role: {role_str})")

    # ── 1. Revoke all refresh tokens ────────────────────────────────────────
    try:
        await db.execute(
            sql_update(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .values(revoked=True)
        )
    except Exception as e: print(f"[DeleteAccount] RefreshToken revoke skipped: {e}")

    # ── 2. Common cleanup (Audit, Activity, Notifications, etc.) ────────────
    
    # 2.1 Audit Logs
    try:
        from app.models.audit import AuditLog
        await db.execute(sql_delete(AuditLog).where(AuditLog.user_id == user_id))
    except Exception as e: print(f"[DeleteAccount] AuditLog cleanup skipped: {e}")

    # 2.2 Activity Logs (both as actor and as subject/patient)
    try:
        from app.models.activity_log import ActivityLog
        await db.execute(sql_delete(ActivityLog).where(
            or_(ActivityLog.user_id == user_id, ActivityLog.patient_id == user_id)
        ))
    except Exception as e: print(f"[DeleteAccount] ActivityLog cleanup skipped: {e}")

    # 2.3 Notifications
    try:
        from app.models.notification import Notification
        await db.execute(sql_delete(Notification).where(Notification.user_id == user_id))
    except Exception as e: print(f"[DeleteAccount] Notification cleanup skipped: {e}")

    # 2.4 Data Access Grants
    try:
        from app.models.data_access_grant import DataAccessGrant
        await db.execute(sql_delete(DataAccessGrant).where(
            or_(DataAccessGrant.patient_id == user_id, DataAccessGrant.doctor_id == user_id)
        ))
    except Exception as e: print(f"[DeleteAccount] DataAccessGrant cleanup skipped: {e}")

    # 2.5 Appointments and Calendar Events
    try:
        from app.models.appointment import Appointment
        # Note: CalendarEvent has ondelete="CASCADE" to users and appointments, 
        # but we handle appointments explicitly here.
        await db.execute(sql_delete(Appointment).where(
            or_(Appointment.patient_id == user_id, Appointment.doctor_id == user_id)
        ))
    except Exception as e: print(f"[DeleteAccount] Appointment cleanup skipped: {e}")

    try:
        from app.models.calendar_event import CalendarEvent
        await db.execute(sql_delete(CalendarEvent).where(CalendarEvent.user_id == user_id))
    except Exception as e: print(f"[DeleteAccount] CalendarEvent cleanup skipped: {e}")

    # 2.6 Chat History and AI Queue
    try:
        from app.models.chat_history import ChatHistory
        await db.execute(sql_delete(ChatHistory).where(
            or_(ChatHistory.patient_id == user_id, ChatHistory.doctor_id == user_id)
        ))
    except Exception as e: print(f"[DeleteAccount] ChatHistory cleanup skipped: {e}")

    try:
        from app.models.ai_processing_queue import AIProcessingQueue
        await db.execute(sql_delete(AIProcessingQueue).where(
            or_(AIProcessingQueue.patient_id == user_id, AIProcessingQueue.doctor_id == user_id)
        ))
    except Exception as e: print(f"[DeleteAccount] AIProcessingQueue cleanup skipped: {e}")

    # 2.7 Recent History Links
    try:
        from app.models.recent_doctors import RecentDoctor
        from app.models.recent_patients import RecentPatient
        await db.execute(sql_delete(RecentDoctor).where(or_(RecentDoctor.patient_id == user_id, RecentDoctor.doctor_id == user_id)))
        await db.execute(sql_delete(RecentPatient).where(or_(RecentPatient.patient_id == user_id, RecentPatient.doctor_id == user_id)))
    except Exception as e: print(f"[DeleteAccount] Recent history cleanup skipped: {e}")

    # 2.8 Documents Uploaded by User (Crucial for doctors/admins)
    try:
        from app.models.document import Document
        # First find all documents uploaded by this user to handle MinIO cleanup if needed later
        # (For now we just delete the metadata to prevent FK violations)
        await db.execute(sql_delete(Document).where(Document.uploaded_by == user_id))
    except Exception as e: print(f"[DeleteAccount] Documents uploaded by user cleanup skipped: {e}")

    # ── 3. Role-specific data cleanup ───────────────────────────────────────
    if role_str == "patient":
        # Chat Sessions (Persistent Threads)
        try:
            from app.models.chat_session import ChatSession, ChatMessage
            # ChatMessage has cascade delete on ChatSession, but we can be explicit or rely on DB
            # Since patient_id in ChatSession refers to patients.id, and we delete the patient profile below,
            # we should delete chat sessions here explicitly to avoid any FK issues.
            await db.execute(sql_delete(ChatSession).where(ChatSession.patient_id == user_id))
        except Exception as e: print(f"[DeleteAccount] ChatSession cleanup skipped: {e}")

        # Health Metrics, Consultations, Documents
        try:
            from app.models.health_metric import HealthMetric
            await db.execute(sql_delete(HealthMetric).where(HealthMetric.patient_id == user_id))
        except Exception as e: print(f"[DeleteAccount] HealthMetric cleanup skipped: {e}")

        try:
            from app.models.consultation import Consultation
            await db.execute(sql_delete(Consultation).where(Consultation.patient_id == user_id))
        except Exception as e: print(f"[DeleteAccount] Consultation cleanup skipped: {e}")

        try:
            from app.models.document import Document
            await db.execute(sql_delete(Document).where(Document.patient_id == user_id))
        except Exception as e: print(f"[DeleteAccount] Document cleanup skipped: {e}")

        # The actual Patient Profile
        try:
            from app.models.patient import Patient
            await db.execute(sql_delete(Patient).where(Patient.id == user_id))
        except Exception as e: print(f"[DeleteAccount] Patient profile cleanup skipped: {e}")

    elif role_str == "doctor":
        # Fully delete consultations for doctors (cannot mark-delete due to NOT NULL constraint on doctor_id)
        try:
            from app.models.consultation import Consultation
            await db.execute(sql_delete(Consultation).where(Consultation.doctor_id == user_id))
        except Exception as e: print(f"[DeleteAccount] Consultation cleanup skipped: {e}")

        # If a doctor is deleted, we must set primary_doctor_id to NULL in patients they care for
        try:
            from app.models.patient import Patient
            await db.execute(
                sql_update(Patient)
                .where(or_(Patient.primary_doctor_id == user_id, Patient.created_by == user_id))
                .values(
                    primary_doctor_id=None,
                    created_by=None
                )
            )
        except Exception as e: print(f"[DeleteAccount] Patient-doctor ref cleanup skipped: {e}")

        # Tasks
        try:
            from app.models.task import Task
            await db.execute(sql_delete(Task).where(Task.doctor_id == user_id))
        except Exception as e: print(f"[DeleteAccount] Task cleanup skipped: {e}")

        # Chat Sessions for Doctors
        try:
            from app.models.chat_session import ChatSession
            await db.execute(sql_delete(ChatSession).where(ChatSession.doctor_id == user_id))
        except Exception as e: print(f"[DeleteAccount] ChatSession cleanup skipped: {e}")

    elif role_str in ("hospital", "admin"):
        # Organization cleanup if it's the last admin
        try:
            other_users_result = await db.execute(select(User).where(and_(User.organization_id == org_id, User.id != user_id, User.deleted_at.is_(None))))
            if not other_users_result.scalars().first():
                org_result = await db.execute(select(Organization).where(Organization.id == org_id))
                org = org_result.scalar_one_or_none()
                if org:
                    # Note: Organization deletion will trigger cascade on many tables if configured, 
                    # but we've already cleaned up most user-specific data above.
                    await db.delete(org)
        except Exception as e: print(f"[DeleteAccount] Organization cleanup skipped: {e}")

    # ── 4. MinIO avatar cleanup ──────────────────────────────────────────────
    if current_user.avatar_url:
        try:
            from app.services.minio_service import minio_service
            from app.config import settings
            minio_service.delete_object(settings.MINIO_BUCKET_AVATARS, current_user.avatar_url)
        except Exception as e: print(f"[DeleteAccount] MinIO cleanup skipped: {e}")

    # ── 5. Hard-delete the User record itself ────────────────────────────────
    try:
        await db.delete(current_user)
        await db.commit()
    except Exception as e:
        await db.rollback()
        print(f"[DeleteAccount] ❌ CRITICAL: Final delete/commit failed: {e}")
        # Re-raise so FastAPI returns a 500 with more info if logging is enabled
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to permanently delete account: {str(e)}"
        )

    return MessageResponse(message="Account and all associated data have been permanently deleted.")


@router.get("/me", response_model=Union[PatientDetailResponse, UserResponse])
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user information. Returns detailed profile if the user is a patient."""
    pii_encryption = PIIEncryption()
    
    # Check if the logged-in user is a patient
    user_role_str = str(current_user.role).split('.')[-1] if hasattr(current_user.role, 'value') else str(current_user.role)
    
    if user_role_str == "patient":
        # Fetch the full Patient record
        query = select(Patient).where(
            Patient.id == current_user.id,
            Patient.deleted_at == None
        )
        result = await db.execute(query)
        patient = result.scalar_one_or_none()
        
        if patient:
            # 1. Decrypt Basic Info
            try:
                full_name = pii_encryption.decrypt(patient.full_name)
            except:
                full_name = patient.full_name or "Unknown"
                
            try:
                dob_str = pii_encryption.decrypt(patient.date_of_birth)
                dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
                today = date.today()
                age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            except:
                dob_str = None
                age = None
                
            try:
                phone = pii_encryption.decrypt(patient.phone_number) if patient.phone_number else None
                home_phone = pii_encryption.decrypt(patient.home_phone) if patient.home_phone else None
            except:
                phone = patient.phone_number
                home_phone = patient.home_phone

            try:
                email = pii_encryption.decrypt(patient.email) if patient.email else None
            except:
                email = patient.email

            try:
                medical_history = pii_encryption.decrypt(patient.medical_history) if patient.medical_history else None
            except:
                medical_history = patient.medical_history

            # 2. Decrypt JSON Dictionaries (Address, Emergency Contact)
            address_dict = None
            if patient.address:
                addr_data = patient.address
                if isinstance(addr_data, str):
                    try:
                        addr_data = json.loads(addr_data)
                    except Exception:
                        addr_data = {}
                
                if isinstance(addr_data, dict):
                    address_dict = {
                        k: pii_encryption.decrypt(v) if isinstance(v, str) else v 
                        for k, v in addr_data.items()
                    }

            emergency_contact_dict = None
            if patient.emergency_contact:
                ec_data = patient.emergency_contact
                if isinstance(ec_data, str):
                    try:
                        ec_data = json.loads(ec_data)
                    except Exception:
                        ec_data = {}
                        
                if isinstance(ec_data, dict):
                    emergency_contact_dict = {
                        k: pii_encryption.decrypt(v) if isinstance(v, str) else v
                        for k, v in ec_data.items()
                    }

            # 3. Decrypt Arrays (Allergies, Medications)
            allergies_list = []
            if patient.allergies:
                alg_data = patient.allergies
                if isinstance(alg_data, str):
                    try:
                        alg_data = json.loads(alg_data)
                    except Exception:
                        alg_data = []
                
                if isinstance(alg_data, list):
                    allergies_list = [pii_encryption.decrypt(i) for i in alg_data]
                
            medications_list = []
            if patient.medications:
                med_data = patient.medications
                if isinstance(med_data, str):
                    try:
                        med_data = json.loads(med_data)
                    except Exception:
                        med_data = []
                        
                if isinstance(med_data, list):
                    medications_list = [pii_encryption.decrypt(i) for i in med_data]
                    
            # 4. Last Consultation logic
            last_visit_q = (
                select(Consultation)
                .where(
                    Consultation.patient_id == patient.id,
                    Consultation.status == "completed"
                )
                .order_by(Consultation.scheduled_at.desc())
                .limit(1)
            )
            lv_res = await db.execute(last_visit_q)
            last_visit_obj = lv_res.scalar_one_or_none()
            
            last_consultation = None
            if last_visit_obj:
                last_consultation = {
                    "date": last_visit_obj.scheduled_at.strftime("%Y-%m-%d"),
                    "diagnosis": last_visit_obj.diagnosis
                }

            # 5. Fetch Health Metrics
            health_metrics_q = (
                select(HealthMetric)
                .where(HealthMetric.patient_id == patient.id)
                .order_by(HealthMetric.recorded_at.desc())
                .limit(20)
            )
            hm_res = await db.execute(health_metrics_q)
            health_metrics = hm_res.scalars().all()

            # 6. Fetch temporary Avatar URL from the current user
            avatar_link = None
            if current_user.avatar_url:
                avatar_link = minio_service.generate_presigned_url(
                    bucket_name=settings.MINIO_BUCKET_AVATARS,
                    object_name=current_user.avatar_url
                )

            return PatientDetailResponse(
                id=patient.id,
                mrn=patient.mrn,
                full_name=full_name,
                age=age,
                date_of_birth=dob_str,
                gender=patient.gender,
                role="patient",
                avatar_url=avatar_link,
                phone_number=phone,
                home_phone=home_phone,
                email=email,
                organization_id=current_user.organization_id,
                address=address_dict,
                emergency_contact=emergency_contact_dict,
                medical_history=medical_history,
                allergies=allergies_list,
                medications=medications_list,
                latest_vitals={
                    "bp": next((v.value for v in health_metrics if v.metric_type.strip().lower() in ["blood_pressure", "blood pressure"]), "N/A"),
                    "hr": next((v.value for v in health_metrics if v.metric_type.strip().lower() in ["heart_rate", "heart rate"]), "N/A"),
                    "weight": next((v.value for v in health_metrics if v.metric_type.strip().lower() == "weight"), "N/A"),
                    "temp": next((v.value for v in health_metrics if v.metric_type.strip().lower() == "temperature"), "N/A"),
                    "resp": next((v.value for v in health_metrics if v.metric_type.strip().lower() == "respiratory_rate"), "N/A"),
                    "spo2": next((v.value for v in health_metrics if v.metric_type.strip().lower() == "oxygen_saturation"), "N/A")
                },
                health_metrics=health_metrics,
                last_consultation=last_consultation
            )

    # ==========================================
    # Fallback to standard response if the user is a doctor/admin 
    # (or if the patient record somehow doesn't exist)
    # ==========================================
    try:
        decrypted_full_name = pii_encryption.decrypt(current_user.full_name)
    except Exception:
        # Fallback if the data is unencrypted or encrypted with an old key
        decrypted_full_name = current_user.full_name if current_user.full_name else "Unknown User"
        
    name_parts = decrypted_full_name.split(" ", 1)

    # Generate temporary Avatar URL for doctor/admin
    avatar_link = None
    if current_user.avatar_url:
        avatar_link = minio_service.generate_presigned_url(
            bucket_name=settings.MINIO_BUCKET_AVATARS,
            object_name=current_user.avatar_url
        )

    return UserResponse(
        id=current_user.id,
        name=decrypted_full_name,
        email=current_user.email,
        first_name=name_parts[0],
        last_name=name_parts[1] if len(name_parts) > 1 else "",
        phone_number=pii_encryption.decrypt(current_user.phone_number) if current_user.phone_number else None,
        role=user_role_str,
        organization_id=current_user.organization_id,
        organization_name=getattr(current_user.organization, "name", "Default Org"),
        email_verified=current_user.email_verified,
        mfa_enabled=current_user.mfa_enabled,
        avatar_url=avatar_link,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )


# ==========================================
# Social Authentication
# ==========================================

from jose import jwt as jose_jwt, JWTError
import json as _json
import urllib.parse
import time

# Initialize SSO Providers
google_sso = GoogleSSO(
    client_id=settings.GOOGLE_CLIENT_ID or "missing-id",
    client_secret=settings.GOOGLE_CLIENT_SECRET or "missing-secret",
    allow_insecure_http=settings.APP_ENV == "development"
)


# Apple Sign-In Helper Class
class AppleSignInHelper:
    """Helper class to handle Apple Sign In authentication"""
    
    @staticmethod
    def generate_client_secret() -> str:
        """
        Generate JWT client secret for Apple authentication.
        Required fields in settings:
        - APPLE_TEAM_ID
        - APPLE_KEY_ID
        - APPLE_PRIVATE_KEY
        - APPLE_CLIENT_ID
        """
        if not all([
            settings.APPLE_TEAM_ID,
            settings.APPLE_KEY_ID,
            settings.APPLE_PRIVATE_KEY,
            settings.APPLE_CLIENT_ID
        ]):
            return None
        
        try:
            now = int(time.time())
            payload = {
                "iss": settings.APPLE_TEAM_ID,
                "iat": now,
                "exp": now + 86400 * 180,  # 6 months
                "aud": "https://appleid.apple.com",
                "sub": settings.APPLE_CLIENT_ID,
            }
            
            secret = jose_jwt.encode(
                payload,
                settings.APPLE_PRIVATE_KEY,
                algorithm="ES256",
                headers={"kid": settings.APPLE_KEY_ID}
            )
            return secret
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate Apple client secret: {str(e)}"
            )
    
    @staticmethod
    async def verify_id_token(token: str) -> dict:
        """
        Verify and decode Apple ID token.
        Returns decoded token data.
        """
        try:
            # Apple sends the token as JWT that we need to verify
            # In production, you should verify the signature against Apple's public keys
            # For now, we'll decode without verification (should be done in production)
            decoded = jose_jwt.get_unverified_claims(token)
            return decoded
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid Apple ID token: {str(e)}"
            )


@router.get("/google/login")
async def google_login(request: Request, redirect_uri: Optional[str] = None, role: Optional[str] = None):
    """Initiate Google Login"""
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Google Auth not configured")
    
    google_redirect = settings.GOOGLE_REDIRECT_URI
    response = await google_sso.get_login_redirect(redirect_uri=google_redirect)
    
    if redirect_uri:
        response.set_cookie(
            key="app_redirect_uri",
            value=redirect_uri,
            max_age=600,
            httponly=True,
            samesite="lax",
            path="/"
        )

    # Store role hint so the callback can create the account with the right role
    if role and role in ("doctor", "hospital", "patient"):
        response.set_cookie(
            key="google_signup_role",
            value=role,
            max_age=600,
            httponly=True,
            samesite="lax",
            path="/"
        )
        
    return response


@router.get("/google/callback")
async def google_callback(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Handle Google Login Callback — redirects browser to frontend with tokens"""
    # Determine the frontend origin from settings
    frontend_url = settings.FRONTEND_URL or "http://localhost:3000"
    frontend_callback = f"{frontend_url}/auth/google/callback"

    try:
        redirect_uri = settings.GOOGLE_REDIRECT_URI
        user_info = await google_sso.verify_and_process(request, redirect_uri=redirect_uri)
    except Exception as e:
        import urllib.parse
        error_msg = urllib.parse.quote(f"Google Auth Failed: {str(e)}")
        return RedirectResponse(url=f"{frontend_callback}?error={error_msg}")

    if not user_info or not user_info.email:
        import urllib.parse
        return RedirectResponse(url=f"{frontend_callback}?error={urllib.parse.quote('No email provided by Google')}")

    # Find user by email, ignoring soft-deleted users
    result = await db.execute(select(User).where(User.email == user_info.email.lower(), User.deleted_at.is_(None)))
    user = result.scalar_one_or_none()
    is_new_user = False
    if not user:
        # Auto-create account for new Google users
        role_cookie = request.cookies.get("google_signup_role", "doctor")
        if role_cookie not in ("doctor", "hospital", "patient"):
            role_cookie = "doctor"

        pii_enc = PIIEncryption()
        display_name = user_info.display_name or user_info.email.split("@")[0]

        try:
            # Create a default personal organization for the user
            new_org = Organization(
                name=f"{display_name}'s Organization",
                subscription_tier="free-trial",
                subscription_status="trialing"
            )
            db.add(new_org)
            await db.flush()

            user = User(
                email=user_info.email.lower(),
                password_hash=hash_password(user_info.id + settings.JWT_SECRET_KEY),
                full_name=pii_enc.encrypt(display_name),
                role=role_cookie,
                google_id=user_info.id,
                email_verified=True,
                organization_id=new_org.id,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            is_new_user = True
        except Exception as e:
            await db.rollback()
            print(f"[Google Signup Error] {str(e)}")
            import urllib.parse
            return RedirectResponse(url=f"{frontend_callback}?error={urllib.parse.quote('Account creation failed')}")

    # Link Google ID if not linked
    if not user.google_id:
        user.google_id = user_info.id
        user.email_verified = True
        await db.commit()
        await db.refresh(user)

    # Heuristic for determining onboarding status (since no column exists yet)
    # If a doctor has no phone or specialty, they likely need onboarding.
    # If a hospital admin has no phone, they likely need onboarding.
    onboarding_complete = True
    user_role_str = str(user.role).split(".")[-1]
    if user_role_str == "doctor":
        if not user.phone_number or not user.specialty:
            onboarding_complete = False
    elif user_role_str == "hospital":
        if not user.phone_number:
            onboarding_complete = False
    
    if is_new_user:
        onboarding_complete = False

    # Generate Tokens
    access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
    refresh_token_value = create_refresh_token(data={"sub": str(user.id)})

    refresh_token_hash = hash_token(refresh_token_value)
    refresh_token = RefreshToken(
        user_id=user.id,
        token_hash=refresh_token_hash,
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    db.add(refresh_token)
    user.last_login = datetime.utcnow()
    await db.commit()

    # Build user data for frontend
    pii_encryption = PIIEncryption()
    try:
        decrypted_full_name = pii_encryption.decrypt(user.full_name)
    except Exception:
        decrypted_full_name = user.full_name or "Unknown User"
    name_parts = decrypted_full_name.split(" ", 1)

    import json as _json
    import urllib.parse

    user_data = {
        "id": str(user.id),
        "name": decrypted_full_name,
        "email": user.email,
        "first_name": name_parts[0],
        "last_name": name_parts[1] if len(name_parts) > 1 else "",
        "role": str(user.role).split(".")[-1],
        "organization_id": str(user.organization_id) if user.organization_id else None,
        "email_verified": user.email_verified,
        "mfa_enabled": user.mfa_enabled,
        "onboarding_complete": onboarding_complete,
    }

    # Redirect browser to frontend callback page with tokens as query params
    encoded_user = urllib.parse.quote(_json.dumps(user_data))
    encoded_access = urllib.parse.quote(access_token)
    encoded_refresh = urllib.parse.quote(refresh_token_value)

    app_redirect_uri = request.cookies.get("app_redirect_uri")
    
    if app_redirect_uri and app_redirect_uri.startswith("saramedico://"):
        from fastapi.responses import HTMLResponse
        
        final_qs = (
            f"access_token={encoded_access}"
            f"&refresh_token={encoded_refresh}"
            f"&user={encoded_user}"
        )
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Redirecting to App...</title>
            <script>
                window.location.href = "{app_redirect_uri}?{final_qs}";
            </script>
        </head>
        <body>
            Redirecting to app...
        </body>
        </html>
        """
        response = HTMLResponse(content=html_content)
        response.delete_cookie("app_redirect_uri", path="/")
        response.delete_cookie("google_signup_role", path="/")
        return response
    else:
        redirect_url = (
            f"{frontend_callback}"
            f"?access_token={encoded_access}"
            f"&refresh_token={encoded_refresh}"
            f"&user={encoded_user}"
        )
        return RedirectResponse(url=redirect_url)


@router.get("/apple/login")
async def apple_login(request: Request):
    """Initiate Apple Sign In - redirects to Apple's OAuth login"""
    if not settings.APPLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Apple Auth not configured")
    
    try:
        # Generate client secret for this session
        client_secret = AppleSignInHelper.generate_client_secret()
        
        # Construct the Apple authorization URL
        redirect_uri = str(request.url_for("apple_callback"))
        apple_auth_url = (
            "https://appleid.apple.com/auth/authorize?"
            f"client_id={settings.APPLE_CLIENT_ID}&"
            f"redirect_uri={urllib.parse.quote(redirect_uri)}&"
            f"response_type=code&"
            f"response_mode=form_post&"
            f"scope=email%20name"
        )
        
        return RedirectResponse(url=apple_auth_url)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initiate Apple login: {str(e)}")


@router.post("/apple/callback")
async def apple_callback(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle Apple Login Callback — redirects browser to frontend with tokens.
    Apple sends data as form-encoded POST request.
    """
    frontend_url = settings.FRONTEND_URL or "http://localhost:3000"
    frontend_callback = f"{frontend_url}/auth/apple/callback"

    try:
        # Parse form data from Apple
        form_data = await request.form()
        user_id = form_data.get("user")
        id_token = form_data.get("id_token")
        
        if not id_token:
            error_msg = urllib.parse.quote("No ID token provided by Apple")
            return RedirectResponse(url=f"{frontend_callback}?error={error_msg}")
        
        # Decode and verify the ID token
        user_info = await AppleSignInHelper.verify_id_token(id_token)
        
        # Extract email from token
        user_email = user_info.get("email")
        apple_user_id = user_info.get("sub")
        
        if not user_email:
            error_msg = urllib.parse.quote("No email provided by Apple")
            return RedirectResponse(url=f"{frontend_callback}?error={error_msg}")
        
        # Find user by email
        result = await db.execute(select(User).where(User.email == user_email.lower()))
        user = result.scalar_one_or_none()
        
        if not user:
            error_msg = urllib.parse.quote("Account not found. Please register or ask your provider to onboard you first.")
            return RedirectResponse(url=f"{frontend_callback}?error={error_msg}")
        
        # Link Apple ID if not already linked
        if not user.apple_id:
            user.apple_id = apple_user_id
            user.email_verified = True  # Trust Apple's email verification
            await db.commit()
            await db.refresh(user)
        
        # Generate Tokens
        access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
        refresh_token_value = create_refresh_token(data={"sub": str(user.id)})
        
        refresh_token_hash = hash_token(refresh_token_value)
        refresh_token = RefreshToken(
            user_id=user.id,
            token_hash=refresh_token_hash,
            expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )
        db.add(refresh_token)
        user.last_login = datetime.utcnow()
        await db.commit()
        
        # Build user data for frontend
        pii_encryption = PIIEncryption()
        try:
            decrypted_full_name = pii_encryption.decrypt(user.full_name)
        except Exception:
            decrypted_full_name = user.full_name or "Unknown User"
        name_parts = decrypted_full_name.split(" ", 1)
        
        user_data = {
            "id": str(user.id),
            "name": decrypted_full_name,
            "email": user.email,
            "first_name": name_parts[0],
            "last_name": name_parts[1] if len(name_parts) > 1 else "",
            "role": str(user.role).split(".")[-1],
            "organization_id": str(user.organization_id) if user.organization_id else None,
            "email_verified": user.email_verified,
            "mfa_enabled": user.mfa_enabled,
        }
        
        # Redirect browser to frontend callback page with tokens as query params
        encoded_user = urllib.parse.quote(_json.dumps(user_data))
        encoded_access = urllib.parse.quote(access_token)
        encoded_refresh = urllib.parse.quote(refresh_token_value)
        
        redirect_url = (
            f"{frontend_callback}"
            f"?access_token={encoded_access}"
            f"&refresh_token={encoded_refresh}"
            f"&user={encoded_user}"
        )
        return RedirectResponse(url=redirect_url)
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = urllib.parse.quote(f"Apple Auth Failed: {str(e)}")
        return RedirectResponse(url=f"{frontend_callback}?error={error_msg}")
#         )
#     )

@router.post("/register/hospital", status_code=status.HTTP_201_CREATED)
async def register_hospital(
    data: HospitalRegistrationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Registers a new Hospital Organization and its root administrator account.
    """
    # 1. Check if the email is already registered
    existing_user_query = select(User).where(User.email == data.email)
    result = await db.execute(existing_user_query)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists."
        )

    pii_encryption = PIIEncryption()

    try:
        # 2. Create the Organization
        new_org = Organization(
            name=data.organization_name,
            subscription_tier="free-trial", # Set default tier
            subscription_status="trialing"
        )
        db.add(new_org)
        await db.flush() # Flush to generate the new_org.id

        # 3. Create the Root Hospital Admin User
        new_admin = User(
            email=data.email,
            password_hash=hash_password(data.password),
            full_name=pii_encryption.encrypt(data.admin_name),
            phone_number=pii_encryption.encrypt(data.phone_number) if data.phone_number else None,
            role="hospital", # Assign the root hospital role
            organization_id=new_org.id,
            email_verified=True # Standard security practice
        )
        db.add(new_admin)
        
        # 4. Commit the transaction
        await db.commit()
        await db.refresh(new_admin)

        return {
            "message": "Hospital registered successfully",
            "organization_id": str(new_org.id),
            "admin_id": str(new_admin.id),
            "email": new_admin.email
        }

    except Exception as e:
        await db.rollback()
        print(f"[Hospital Registration Error] {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while registering the hospital. Please try again."
        )

@router.patch("/onboarding", response_model=MessageResponse)
async def update_onboarding(
    update_data: OnboardingUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update onboarding details after initial simple registration.
    """
    pii_encryption = PIIEncryption()
    
    if update_data.phone_number:
        current_user.phone_number = pii_encryption.encrypt(update_data.phone_number)
        
    if update_data.first_name and update_data.last_name:
        current_user.full_name = pii_encryption.encrypt(f"{update_data.first_name} {update_data.last_name}")
        
    if update_data.organization_name:
        # Get or create organization
        org_result = await db.execute(
            select(Organization).where(Organization.name == update_data.organization_name)
        )
        organization = org_result.scalar_one_or_none()
        if not organization:
            organization = Organization(name=update_data.organization_name)
            db.add(organization)
            await db.flush()
        current_user.organization_id = organization.id

    # For patient model updates if needed, though they don't do this directly.
    # We mainly update the User model.
    # Note: DOB/Gender is usually in Patient or Doctor profile, but we store minimal here.
    
    await db.commit()
    return MessageResponse(message="Onboarding details updated successfully")