"""Authentication API endpoints"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from fastapi import Request
from fastapi_sso.sso.google import GoogleSSO
# from fastapi_sso.sso.apple import AppleSSO

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
    stmt = update(RefreshToken).where(RefreshToken.token_hash == token_hash)
    
    if current_user:
        stmt = stmt.where(RefreshToken.user_id == current_user.id)
        
    await db.execute(stmt)
    await db.commit()
    
    return MessageResponse(message="Logged out successfully")


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
            except:
                phone = patient.phone_number

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
                email=email,
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
        role=current_user.role,
        organization_id=current_user.organization_id,
        email_verified=current_user.email_verified,
        mfa_enabled=current_user.mfa_enabled,
        avatar_url=avatar_link,
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
            phone_number=pii_encryption.encrypt(data.phone_number),
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