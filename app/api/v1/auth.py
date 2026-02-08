"""Authentication API endpoints"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import Request
from fastapi_sso.sso.google import GoogleSSO
# from fastapi_sso.sso.apple import AppleSSO

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

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
    
    # Decrypt name for response
    decrypted_full_name = pii_encryption.decrypt(user.full_name)
    name_parts = decrypted_full_name.split(" ", 1)
    
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
    
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else ""

    return UserResponse(
        id=user.id,
        name=decrypted_full_name,
        email=user.email,
        first_name=first_name,
        last_name=last_name,
        phone_number=pii_encryption.decrypt(user.phone_number) if user.phone_number else None,
        role=user.role,
        organization_id=user.organization_id,
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
    result = await db.execute(
        select(User).where(
            User.email == credentials.email.lower(),
            User.deleted_at.is_(None)
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
    decrypted_full_name = pii_encryption.decrypt(user.full_name)
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
    
    result = await db.execute(
        select(User).where(User.id == user_uuid, User.deleted_at.is_(None))
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
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token_value,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            email=user.email,
            first_name=pii_encryption.decrypt(user.first_name),
            last_name=pii_encryption.decrypt(user.last_name),
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


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: RefreshTokenRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Logout by revoking refresh token"""
    # Hash and revoke the refresh token
    token_hash = hash_token(request.refresh_token)
    
    await db.execute(
        update(RefreshToken)
        .where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.user_id == current_user.id
        )
        .values(revoked=True)
    )
    
    await db.commit()
    
    return MessageResponse(message="Logged out successfully")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """Get current user information"""
    pii_encryption = PIIEncryption()
    
    decrypted_full_name = pii_encryption.decrypt(current_user.full_name)
    name_parts = decrypted_full_name.split(" ", 1)
    
    return UserResponse(
        id=current_user.id,
        name=decrypted_full_name,
        email=current_user.email,
        first_name=name_parts[0],
        last_name=name_parts[1] if len(name_parts) > 1 else "",
        phone_number=pii_encryption.decrypt(current_user.phone_number) if current_user.phone_number else None,
        role=current_user.role,
        organization_id=current_user.organization_id,
        email_verified=current_user.email_verified,
        mfa_enabled=current_user.mfa_enabled,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )


# ==========================================
# Social Authentication
# ==========================================

# Initialize SSO Providers
# Note: For production, ensure allow_insecure_http is False
google_sso = GoogleSSO(
    client_id=settings.GOOGLE_CLIENT_ID or "missing-id",
    client_secret=settings.GOOGLE_CLIENT_SECRET or "missing-secret",
    allow_insecure_http=settings.APP_ENV == "development"
)

# apple_sso = AppleSSO(
#     client_id=settings.APPLE_CLIENT_ID or "missing-id",
#     client_secret=settings.APPLE_CLIENT_SECRET or "missing-secret",
#     allow_insecure_http=settings.APP_ENV == "development"
# )

@router.get("/google/login")
async def google_login(request: Request):
    """Initiate Google Login"""
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Google Auth not configured")
    
    # Construct callback URL dynamically to match the request host
    # e.g., http://localhost:8000/api/v1/auth/google/callback
    redirect_uri = str(request.url_for("google_callback"))
    return await google_sso.get_login_redirect(redirect_uri=redirect_uri)


@router.get("/google/callback", response_model=LoginResponse)
async def google_callback(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Handle Google Login Callback"""
    try:
        user_info = await google_sso.verify_and_process(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Google Auth Failed: {str(e)}")

    if not user_info or not user_info.email:
        raise HTTPException(status_code=400, detail="No email provided by Google")

    # Find user by email
    result = await db.execute(select(User).where(User.email == user_info.email.lower()))
    user = result.scalar_one_or_none()

    if not user:
        # STRICT SECURITY: Do not auto-register.
        # Patients must be added by doctors first.
        # Doctors must register via the specific doctor flow.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account not found. Please register or ask your provider to onboard you first."
        )

    # Link Google ID if not linked
    if not user.google_id:
        user.google_id = user_info.id
        user.email_verified = True # Trust Google verification
        await db.commit()
        await db.refresh(user)

    # Generate Tokens (reuse existing logic)
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

    # Prepare response
    pii_encryption = PIIEncryption()
    decrypted_full_name = pii_encryption.decrypt(user.full_name)
    name_parts = decrypted_full_name.split(" ", 1)

    return LoginResponse(
        success=True,
        access_token=access_token,
        refresh_token=refresh_token_value,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            name=decrypted_full_name,
            email=user.email,
            first_name=name_parts[0],
            last_name=name_parts[1] if len(name_parts) > 1 else "",
            role=user.role,
            organization_id=user.organization_id,
            email_verified=user.email_verified,
            mfa_enabled=user.mfa_enabled,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    )


# @router.get("/apple/login")
# async def apple_login(request: Request):
#     """Initiate Apple Login"""
#     if not settings.APPLE_CLIENT_ID:
#         raise HTTPException(status_code=500, detail="Apple Auth not configured")
        
#     redirect_uri = str(request.url_for("apple_callback"))
#     return await apple_sso.get_login_redirect(redirect_uri=redirect_uri)


# @router.get("/apple/callback", response_model=LoginResponse)
# async def apple_callback(
#     request: Request,
#     db: AsyncSession = Depends(get_db)
# ):
#     """Handle Apple Login Callback"""
#     try:
#         user_info = await apple_sso.verify_and_process(request)
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=f"Apple Auth Failed: {str(e)}")

#     if not user_info or not user_info.email:
#          raise HTTPException(status_code=400, detail="No email provided by Apple")

#     # Find user
#     result = await db.execute(select(User).where(User.email == user_info.email.lower()))
#     user = result.scalar_one_or_none()

#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Account not found. Please register or ask your provider to onboard you first."
#         )

#     # Link Apple ID
#     if not user.apple_id:
#         user.apple_id = user_info.id
#         await db.commit()
    
#     # Generate Tokens (reuse same logic as Google)
#     access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
#     refresh_token_value = create_refresh_token(data={"sub": str(user.id)})
    
#     refresh_token_hash = hash_token(refresh_token_value)
#     refresh_token = RefreshToken(
#         user_id=user.id,
#         token_hash=refresh_token_hash,
#         expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
#     )
#     db.add(refresh_token)
#     user.last_login = datetime.utcnow()
#     await db.commit()

#     pii_encryption = PIIEncryption()
#     decrypted_full_name = pii_encryption.decrypt(user.full_name)
#     name_parts = decrypted_full_name.split(" ", 1)

#     return LoginResponse(
#         success=True,
#         access_token=access_token,
#         refresh_token=refresh_token_value,
#         token_type="bearer",
#         user=UserResponse(
#             id=user.id,
#             name=decrypted_full_name,
#             email=user.email,
#             first_name=name_parts[0],
#             last_name=name_parts[1] if len(name_parts) > 1 else "",
#             role=user.role,
#             organization_id=user.organization_id,
#             email_verified=user.email_verified,
#             mfa_enabled=user.mfa_enabled,
#             created_at=user.created_at,
#             updated_at=user.updated_at
#         )
#     )