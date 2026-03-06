from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from fastapi import BackgroundTasks
from app.core.security import hash_password, pii_encryption
from app.schemas.hospital import DoctorCreateRequest, DoctorCreateResponse, DoctorUpdateRequest, DoctorUpdateResponse
from app.services.email import send_doctor_credentials_email
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user, get_organization_id
from app.database import get_db
from app.models.user import User
from app.schemas.hospital import HospitalOverviewResponse, HospitalDirectoryResponse, HospitalPatientsResponse, HospitalStaffResponse
from app.services.hospital_service import HospitalService

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
        email=request.email,
        password_hash=hash_password(request.password),
        full_name=pii_encryption.encrypt(request.name),
        role="doctor",
        organization_id=organization_id,
        email_verified=True,  # Trust the hospital's creation
        department=request.department,
        department_role=request.department_role,
        license_number=pii_encryption.encrypt(request.license_number)
    )
    
    db.add(new_doctor)
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
        doc_check = await db.execute(
            select(User).where(
                User.role == "doctor", 
                User.organization_id == organization_id,
                User.id != doctor_id # Exclude the current doctor from the check
            )
        )
        existing_doctors = doc_check.scalars().all()
        
        for doc in existing_doctors:
            if doc.license_number:
                try:
                    decrypted_license = pii_encryption.decrypt(doc.license_number)
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

    # 5. Save changes
    await db.commit()

    return DoctorUpdateResponse(
        message="Doctor details updated successfully.",
        doctor_id=str(doctor.id)
    )