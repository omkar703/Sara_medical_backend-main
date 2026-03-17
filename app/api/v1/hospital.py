import os
import uuid
from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from fastapi import BackgroundTasks
from app.core.security import hash_password, pii_encryption
from app.schemas.hospital import DoctorCreateRequest, DoctorCreateResponse, DoctorUpdateRequest, DoctorUpdateResponse
from app.services.email import send_doctor_credentials_email
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.hospital import PatientRecordsResponse

from app.core.deps import get_current_active_user, get_organization_id
from app.database import get_db
from fastapi import File, UploadFile
from app.models.user import User, Organization
from app.schemas.hospital import (
    HospitalOverviewResponse, 
    HospitalDirectoryResponse, 
    HospitalPatientsResponse, 
    HospitalStaffResponse,
    HospitalAppointmentsOverviewResponse
)
from app.schemas.admin import (
    AllSettingsResponse,
    AdminProfileSchema,
    OrganizationSchema,
    AdminProfileUpdate,
    OrgSettingsUpdate
)
from app.config import settings
from app.services.minio_service import minio_service
from app.services.hospital_service import HospitalService
from app.models.doctor_status import DoctorStatus
from app.schemas.doctor_status import HospitalDoctorStatusListResponse, DoctorWithStatusItem
from app.schemas.doctor_status import HospitalDoctorStatusListResponse, DoctorDetailedWithStatusItem

router = APIRouter(prefix="/hospital", tags=["Hospital Dashboard"])

@router.get("/dashboard/overview", response_model=HospitalOverviewResponse)
async def get_hospital_overview(
    current_user: User = Depends(get_current_active_user),
    organization_id: UUID = Depends(get_organization_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the high-level overview metrics and recent activities for the hospital dashboard.
    Requires 'hospital' or 'admin' role.
    """
    # Enforce role permissions securely
    if current_user.role not in ["hospital", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access the hospital dashboard."
        )

    service = HospitalService(db)
    data = await service.get_dashboard_overview(organization_id)
    
    return data

@router.get("/appointments/overview", response_model=HospitalAppointmentsOverviewResponse)
async def get_appointments_overview(
    current_user: User = Depends(get_current_active_user),
    organization_id: UUID = Depends(get_organization_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Get appointments overview metrics including scheduled, accepted, 
    transcriptions in queue, and pending notes.
    Requires 'hospital' or 'admin' role.
    """
    if current_user.role not in ["hospital", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access the appointments overview."
        )

    service = HospitalService(db)
    data = await service.get_appointments_overview(organization_id)
    
    return data

@router.get("/directory", response_model=HospitalDirectoryResponse)
async def get_hospital_directory(
    current_user: User = Depends(get_current_active_user),
    organization_id: UUID = Depends(get_organization_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the directory of all doctors and patients for the hospital.
    Requires 'hospital' or 'admin' role.
    """
    if current_user.role not in ["hospital", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access the hospital directory."
        )

    service = HospitalService(db)
    data = await service.get_hospital_directory(organization_id)
    
    return data

@router.get("/patients", response_model=HospitalPatientsResponse)
async def get_hospital_patients_section(
    current_user: User = Depends(get_current_active_user),
    organization_id: UUID = Depends(get_organization_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the patients section metrics and table data (including last visit).
    Requires 'hospital' or 'admin' role.
    """
    if current_user.role not in ["hospital", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access the hospital patients view."
        )

    service = HospitalService(db)
    data = await service.get_hospital_patients_overview(organization_id)
    
    return data

@router.get("/staff", response_model=HospitalStaffResponse)
async def get_hospital_staff_section(
    current_user: User = Depends(get_current_active_user),
    organization_id: UUID = Depends(get_organization_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the staff management metrics and detailed table data.
    Requires 'hospital' or 'admin' role.
    """
    if current_user.role not in ["hospital", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access the hospital staff view."
        )

    service = HospitalService(db)
    data = await service.get_hospital_staff(organization_id)
    
    return data

@router.post("/doctor/create", response_model=DoctorCreateResponse)
async def create_doctor_account(
    request: DoctorCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    organization_id: UUID = Depends(get_organization_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new doctor account directly from the hospital dashboard.
    Will reject the request if the email or license number is already registered.
    """
    # 1. Enforce Role check (Only Hospital or Admin can perform this)
    if current_user.role not in ["hospital", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to create doctor accounts."
        )

    # 2. Check if the email already exists in the system
    email_check = await db.execute(select(User).where(User.email == request.email))
    if email_check.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address is already registered."
        )

    # 3. Check for existing license numbers (in-memory due to Fernet encryption)
    # Fetch all doctors in the organization to verify license uniqueness
    doc_check = await db.execute(
        select(User).where(User.role == "doctor", User.organization_id == organization_id)
    )
    existing_doctors = doc_check.scalars().all()
    
    for doc in existing_doctors:
        if doc.license_number:
            try:
                decrypted_license = pii_encryption.decrypt(doc.license_number)
                if decrypted_license == request.license_number:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="A doctor with this license number already exists in the system."
                    )
            except Exception:
                continue # Skip if decryption fails on an old/corrupt record

    # 4. Fetch the organization name for the email template
    from app.models.user import Organization
    org_query = await db.execute(select(Organization.name).where(Organization.id == organization_id))
    org_name = org_query.scalar_one_or_none() or "Saramedico Hospital"

    # 5. Create the Doctor Account
    new_doctor = User(
        email=request.email.lower(),
        password_hash=hash_password(request.password),
        full_name=pii_encryption.encrypt(request.name),
        role="doctor",
        organization_id=organization_id,
        email_verified=True,  # Trust the hospital's creation
        is_active=True,
        department=request.department,
        department_role=request.department_role,
        specialty=request.specialty,
        license_number=pii_encryption.encrypt(request.license_number)
    )
    
    db.add(new_doctor)
    await db.flush() # Ensure ID is generated
    
    # Initialize Doctor Status as 'active' by default
    from app.models.doctor_status import DoctorStatus
    new_status = DoctorStatus(doctor_id=new_doctor.id, status="active")
    db.add(new_status)
    
    await db.commit()
    await db.refresh(new_doctor)

    # 6. Send Invitation & Credentials Email
    background_tasks.add_task(
        send_doctor_credentials_email,
        to_email=request.email,
        name=request.name,
        password=request.password,
        department=request.department,
        role=request.department_role,
        org_name=org_name
    )

    return DoctorCreateResponse(
        message="Doctor account created successfully. Credentials have been sent to their email.",
        doctor_id=str(new_doctor.id)
    )
    
@router.patch("/doctor/{doctor_id}", response_model=DoctorUpdateResponse)
async def update_doctor_account(
    doctor_id: UUID,
    request: DoctorUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    organization_id: UUID = Depends(get_organization_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Update an existing doctor's profile from the hospital dashboard.
    Only updates the fields that are provided in the request payload.
    """
    # 1. Enforce Role Check
    if current_user.role not in ["hospital", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to edit doctor accounts."
        )

    # 2. Fetch the target doctor and ensure they belong to this organization
    stmt = select(User).where(
        User.id == doctor_id, 
        User.organization_id == organization_id,
        User.role == "doctor",
        User.deleted_at.is_(None)
    )
    result = await db.execute(stmt)
    doctor = result.scalar_one_or_none()

    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Doctor not found in your organization."
        )

    # 3. Prevent duplicate license numbers if a new one is being set
    if request.license_number:
        # Optimization: only select the license_number column to avoid overhead
        doc_check = await db.execute(
            select(User.license_number).where(
                User.role == "doctor", 
                User.organization_id == organization_id,
                User.id != doctor_id,
                User.license_number.is_not(None)
            )
        )
        existing_licenses = doc_check.scalars().all()
        
        for encrypted_license in existing_licenses:
            try:
                decrypted_license = pii_encryption.decrypt(encrypted_license)
                if decrypted_license == request.license_number:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Another doctor in the system is already using this license number."
                    )
            except Exception:
                continue

    # 4. Apply updates securely
    if request.name is not None:
        doctor.full_name = pii_encryption.encrypt(request.name)
    if request.department is not None:
        doctor.department = request.department
    if request.department_role is not None:
        doctor.department_role = request.department_role
    if request.specialty is not None:
        doctor.specialty = request.specialty
    if request.license_number is not None:
        doctor.license_number = pii_encryption.encrypt(request.license_number)

    # 5. Handle status update via DoctorStatus table
    if request.status is not None:
        status_val = request.status.strip().lower()
        VALID_STATUSES = {"active", "inactive", "on_leave"}
        if status_val not in VALID_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid status '{request.status}'. Must be one of: {', '.join(sorted(VALID_STATUSES))}"
            )

        # Query and update status record cleanly
        status_result = await db.execute(
            select(DoctorStatus).where(DoctorStatus.doctor_id == doctor_id)
        )
        doctor_status_record = status_result.scalar_one_or_none()

        if doctor_status_record:
            doctor_status_record.status = status_val
        else:
            new_status_record = DoctorStatus(doctor_id=doctor_id, status=status_val)
            db.add(new_status_record)

    # 6. Commit all changes
    # The get_db dependency handles a final commit, but we commit here 
    # to catch any database-level constraints issues before returning.
    await db.commit()

    return DoctorUpdateResponse(
        message="Doctor details updated successfully.",
        doctor_id=str(doctor_id)
    )
    
@router.get("/doctors/status", response_model=HospitalDoctorStatusListResponse)
async def get_hospital_doctors_status(
    current_user: User = Depends(get_current_active_user),
    organization_id: UUID = Depends(get_organization_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Get lists of active and inactive doctors for the hospital with all details.
    Strictly filters by the hospital's organization_id.
    Requires 'hospital' or 'admin' role.
    """
    if current_user.role not in ["hospital", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access the hospital status board."
        )

    # Note the specific filter: User.organization_id == organization_id
    stmt = select(User, DoctorStatus.status).outerjoin(
        DoctorStatus, User.id == DoctorStatus.doctor_id
    ).where(
        User.organization_id == organization_id, 
        User.role == "doctor",
        User.deleted_at.is_(None)
    )
    
    result = await db.execute(stmt)
    rows = result.all()

    active_doctors = []
    inactive_doctors = []

    for doc, doc_status_val in rows:
        import logging
        logger = logging.getLogger(__name__)
        
        # 1. Decrypt Name
        try:
            full_name = pii_encryption.decrypt(doc.full_name) if doc.full_name else "Unknown"
        except Exception as e:
            logger.error(f"Failed to decrypt name for doc {doc.id} ({doc.email}): {e}")
            full_name = doc.full_name or "Unknown"
            
        # 2. Decrypt Phone Number
        phone_number = None
        if doc.phone_number:
            try:
                phone_number = pii_encryption.decrypt(doc.phone_number)
            except Exception as e:
                logger.error(f"Failed to decrypt phone for doc {doc.id} ({doc.email}): {e}")
                phone_number = doc.phone_number
                
        # 3. Decrypt License Number
        license_number = None
        if doc.license_number:
            try:
                license_number = pii_encryption.decrypt(doc.license_number)
            except Exception as e:
                logger.error(f"Failed to decrypt license for doc {doc.id} ({doc.email}): {e}")
                license_number = doc.license_number

        # Default to inactive if the doctor hasn't explicitly set a status yet
        current_status = doc_status_val if doc_status_val else "inactive"
        
        item = DoctorDetailedWithStatusItem(
            id=doc.id,
            name=full_name,
            email=doc.email,
            specialty=doc.specialty,
            photo_url=doc.avatar_url,
            department=doc.department,
            department_role=doc.department_role,
            phone_number=phone_number,
            license_number=license_number,
            created_at=doc.created_at,
            last_login=doc.last_login,
            status=current_status
        )
        
        if current_status == "active":
            active_doctors.append(item)
        else:
            inactive_doctors.append(item)
            
    return HospitalDoctorStatusListResponse(
        active_doctors=active_doctors,
        inactive_doctors=inactive_doctors
    )

@router.get("/patients/{patient_id}/records", response_model=PatientRecordsResponse)
async def get_patient_health_records(
    patient_id: UUID,
    current_user: User = Depends(get_current_active_user),
    organization_id: UUID = Depends(get_organization_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all health metrics (vitals) and documents for a specific patient.
    Requires 'hospital' or 'admin' role.
    """
    if current_user.role not in ["hospital", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access patient records."
        )

    service = HospitalService(db)
    try:
        data = await service.get_patient_records(organization_id, patient_id)
        return data
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.get("/patients/documents/{document_id}/url")
async def get_patient_document_url(
    document_id: UUID,
    disposition: str = "inline", # 'inline' for view, 'attachment' for download
    current_user: User = Depends(get_current_active_user),
    organization_id: UUID = Depends(get_organization_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a presigned URL for viewing or downloading a patient document.
    """
    if current_user.role not in ["hospital", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access patient records."
        )

    # 1. Fetch document and verify ownership/org
    from app.models.document import Document
    stmt = select(Document).where(
        Document.id == document_id,
        Document.organization_id == organization_id,
        Document.deleted_at.is_(None)
    )
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()
    
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found."
        )

    # 2. Generate URL
    from app.services.minio_service import minio_service
    from app.config import settings
    
    # Optional: Customize content-disposition if downloading
    # Minio presigned_get_object doesn't directly expose response-headers in the simple wrapper,
    # but our generate_presigned_url is a wrapper itself. 
    # Let's check minio_service.py if it supports extra params.
    # If not, the current generate_presigned_url just gives a standard GET link.
    
    response_headers = {}
    if disposition == "attachment":
        response_headers["response-content-disposition"] = f'attachment; filename="{doc.file_name}"'
    else:
        response_headers["response-content-disposition"] = "inline"
    
    url = minio_service.generate_presigned_url(
        bucket_name=settings.MINIO_BUCKET_DOCUMENTS,
        object_name=doc.storage_path,
        expiry_seconds=3600,
        response_headers=response_headers
    )

    if not url:
         raise HTTPException(status_code=500, detail="Failed to generate secure link.")

    return {"url": url, "file_name": doc.file_name}

# --- Settings Management (Hospital Specific) ---

@router.get("/settings", response_model=AllSettingsResponse)
async def get_hospital_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Fetch hospital dashboard settings (profile + organization)"""
    if current_user.role not in ["hospital", "admin"]:
        raise HTTPException(status_code=403, detail="Hospital access required")

    # 1. Fetch Organization Info
    result = await db.execute(select(Organization).where(Organization.id == current_user.organization_id))
    org = result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # 2. Prepare Profile Info (Decrypted)
    try:
        display_name = pii_encryption.decrypt(current_user.full_name) if current_user.full_name else "Hospital User"
        display_phone = pii_encryption.decrypt(current_user.phone_number) if current_user.phone_number else None
    except Exception as e:
        print(f"PII Decryption failed: {e}")
        display_name = current_user.full_name or "Hospital User"
        display_phone = current_user.phone_number

    # Generate a preview URL for the avatar if it exists
    avatar_preview = None
    if current_user.avatar_url:
        try:
            avatar_preview = minio_service.generate_presigned_url(
                bucket_name=settings.MINIO_BUCKET_AVATARS,
                object_name=current_user.avatar_url
            )
        except Exception as e:
            print(f"Avatar URL generation failed: {e}")

    return AllSettingsResponse(
        profile=AdminProfileSchema(
            name=display_name,
            full_name=display_name,
            email=current_user.email,
            avatar_url=avatar_preview,
            phone=display_phone,
            phone_number=display_phone
        ),
        organization=OrganizationSchema(
            name=org.name or "Untitled Hospital",
            org_email=org.org_email or "admin@hospital-group.com",
            timezone=org.timezone or "UTC",
            date_format=org.date_format or "DD/MM/YYYY"
        ),
        integrations=[],
        developer={"api_key_name": "Standard Key", "webhook_url": ""},
        backup={"backup_frequency": "daily"}
    )

@router.patch("/settings/profile")
async def update_hospital_profile(
    profile_in: AdminProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update the logged-in hospital user's personal information"""
    if current_user.role not in ["hospital", "admin"]:
        raise HTTPException(status_code=403, detail="Hospital access required")

    
    if profile_in.name:
        current_user.full_name = pii_encryption.encrypt(profile_in.name)
    
    if profile_in.email:
        # Check for email conflicts
        conflict = await db.execute(select(User).where(User.email == profile_in.email, User.id != current_user.id))
        if conflict.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already in use")
        current_user.email = profile_in.email

    if profile_in.phone_number is not None:
        current_user.phone_number = pii_encryption.encrypt(profile_in.phone_number) if profile_in.phone_number else None

    if profile_in.password:
        current_user.password_hash = hash_password(profile_in.password)

    await db.commit()
    return {"message": "Profile updated successfully"}

@router.post("/settings/avatar")
async def upload_hospital_avatar(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Upload and set the hospital user's profile picture"""
    if current_user.role not in ["hospital", "admin"]:
        raise HTTPException(status_code=403, detail="Hospital access required")

    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")

    try:
        file_ext = os.path.splitext(file.filename)[1]
        object_name = f"avatars/{current_user.id}_{uuid.uuid4().hex}{file_ext}"
        
        file_content = await file.read()
        success = minio_service.upload_bytes(
            file_data=file_content,
            bucket_name=settings.MINIO_BUCKET_AVATARS,
            object_name=object_name,
            content_type=file.content_type
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to upload to storage")

        current_user.avatar_url = object_name
        await db.commit()
        
        return {"message": "Avatar updated", "avatar_url": object_name}
    except Exception as e:
        print(f"Avatar upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/settings/organization")
async def update_hospital_organization(
    settings_in: OrgSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update organization-level settings for the hospital"""
    if current_user.role not in ["hospital", "admin"]:
        raise HTTPException(status_code=403, detail="Hospital access required")

    result = await db.execute(select(Organization).where(Organization.id == current_user.organization_id))
    org = result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    if settings_in.name:
        org.name = settings_in.name
    
    if settings_in.timezone:
        org.timezone = settings_in.timezone
    if settings_in.date_format:
        org.date_format = settings_in.date_format
    if settings_in.org_email:
        org.org_email = settings_in.org_email

    await db.commit()
    return {"message": "Organization updated successfully"}