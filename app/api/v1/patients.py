"""Patient API Endpoints"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user, get_organization_id, require_doctor, require_role
from app.database import get_db
from app.models.user import User
from app.models.patient import Patient
from app.schemas.patient import (
    PatientCreate,
    PatientListResponse,
    PatientOnboard,
    PatientResponse,
    PatientUpdate,
)
from app.services.audit_service import log_action
from app.services.patient_service import PatientService
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.health_metric import HealthMetric
from app.schemas.health_metric import HealthMetricResponse
from app.models.recent_doctors import RecentDoctor
from app.schemas.recent_doctors import RecentDoctorResponse
from typing import List

from app.schemas.patient import PatientDetailResponse
from app.models.consultation import Consultation
from datetime import date, datetime

router = APIRouter(prefix="/patients", tags=["Patients"])


@router.get("", response_model=PatientListResponse)
async def list_patients(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    organization_id: UUID = Depends(get_organization_id),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    """
    List patients for the current user's organization.
    Supports pagination and searching by MRN (and name in future).
    """
    service = PatientService(db)
    result = await service.list_patients(
        organization_id=organization_id,
        page=page,
        limit=limit,
        search=search
    )
    
    # Audit log
    await log_action(
        db=db,
        user_id=current_user.id,
        organization_id=organization_id,
        action="list",
        resource_type="patient",
        resource_id=None,
        request=request,
        metadata={"page": page, "limit": limit, "search": search}
    )
    
    # Rename 'items' key to 'patients' to match schema alias if needed, 
    # but Pydantic alias="patients" on 'items' field handles mapping mapping if we pass 'items' to constructor.
    # Actually PatientListResponse field is `items` aliased as `patients`.
    # Service returns dict with `items`. So passing result directly works.
    
    return result


@router.post("", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    patient_in: PatientOnboard,
    current_user: User = Depends(require_role("doctor")), # Or admin/hospital
    organization_id: UUID = Depends(get_organization_id),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    """
    Onboard a new patient by creating both User account and Patient profile.
    Requires 'doctor', 'admin', or 'hospital' role.
    
    This is the primary patient onboarding endpoint that:
    1. Creates a User account with encrypted credentials
    2. Creates a Patient profile with encrypted PII
    3. Links the two records
    4. Returns patient details
    
    The patient can then log in using the email and password provided.
    """
    from app.core.security import hash_password, PIIEncryption
    from app.models.user import User as UserModel
    from sqlalchemy import select
    
    # Check if user with email already exists
    email_check = await db.execute(
        select(UserModel).where(UserModel.email == patient_in.email.lower())
    )
    if email_check.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Create User account
    pii_encryption = PIIEncryption()
    encrypted_name = pii_encryption.encrypt(patient_in.full_name)
    encrypted_phone = pii_encryption.encrypt(patient_in.phone_number) if patient_in.phone_number else None
    
    new_user = UserModel(
        email=patient_in.email.lower(),
        password_hash=hash_password(patient_in.password),
        full_name=encrypted_name,
        phone_number=encrypted_phone,
        role="patient",
        organization_id=organization_id,
        email_verified=True  # Auto-verify onboarded patients
    )
    db.add(new_user)
    await db.flush()  # Get user ID
    
    # Create Patient profile
    service = PatientService(db)
    patient_data = patient_in.model_dump(exclude={"password"})
    
    patient = await service.create_patient(
        patient_data=patient_data,
        organization_id=organization_id,
        created_by=current_user.id,
        patient_id=new_user.id  # Link to User account
    )
    
    await db.commit()
    
    # Audit log
    await log_action(
        db=db,
        user_id=current_user.id,
        organization_id=organization_id,
        action="onboard",
        resource_type="patient",
        resource_id=patient["id"],
        request=request,
        metadata={"mrn": patient["mrn"], "email": patient_in.email}
    )
    await db.commit()
    
    return patient


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: UUID,
    current_user: User = Depends(get_current_active_user),
    organization_id: UUID = Depends(get_organization_id),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    """
    Get patient details by ID.
    Ensures patient belongs to the same organization.
    """
    service = PatientService(db)
    patient = await service.get_patient(patient_id, organization_id)
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Audit log
    await log_action(
        db=db,
        user_id=current_user.id,
        organization_id=organization_id,
        action="view",
        resource_type="patient",
        resource_id=patient_id,
        request=request
    )
    await db.commit()
    
    return patient


@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: UUID,
    patient_in: PatientUpdate,
    current_user: User = Depends(require_role("doctor")),
    organization_id: UUID = Depends(get_organization_id),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    """
    Update patient details.
    Requires 'doctor' or 'admin' role.
    """
    service = PatientService(db)
    patient_data = patient_in.model_dump(exclude_unset=True)
    
    updated_patient = await service.update_patient(
        patient_id, organization_id, patient_data
    )
    
    if not updated_patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    await db.commit()
    
    # Audit log
    await log_action(
        db=db,
        user_id=current_user.id,
        organization_id=organization_id,
        action="update",
        resource_type="patient",
        resource_id=patient_id,
        request=request,
        metadata={"updated_fields": list(patient_data.keys())}
    )
    await db.commit()
    
    return updated_patient


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(
    patient_id: UUID,
    current_user: User = Depends(require_role("admin")), # Restrict delete to admin? Or doctor too? Roadmap said doctor/admin.
    organization_id: UUID = Depends(get_organization_id),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    """
    Soft delete a patient.
    Requires 'admin' role (stricter than update).
    """
    service = PatientService(db)
    success = await service.delete_patient(patient_id, organization_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    await db.commit()
    
    # Audit log
    await log_action(
        db=db,
        user_id=current_user.id,
        organization_id=organization_id,
        action="delete",
        resource_type="patient",
        resource_id=patient_id,
        request=request
    )
    await db.commit()
    
    return None

@router.get("/{patient_id}/health", response_model=List[HealthMetricResponse])
async def get_patient_health_metrics(
    patient_id: UUID,
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_active_user),
    organization_id: UUID = Depends(get_organization_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Fetch patient's health metrics (Vitals like BP, Heart Rate).
    Returns the most recent metrics first.
    """
    # 1. Verify Patient Exists & Access
    service = PatientService(db)
    patient = await service.get_patient(patient_id, organization_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # 2. Fetch Metrics
    result = await db.execute(
        select(HealthMetric)
        .where(HealthMetric.patient_id == patient_id)
        .order_by(HealthMetric.recorded_at.desc())
        .limit(limit)
    )
    metrics = result.scalars().all()
    
    return metrics

@router.get("/{patient_id}/recent-doctors", response_model=List[RecentDoctorResponse])
async def get_patient_recent_doctors(
    patient_id: UUID,
    current_user: User = Depends(get_current_active_user),
    organization_id: UUID = Depends(get_organization_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Get list of doctors the patient has visited recently.
    """
    # 1. Permission Check (Patient can see own, Doctor/Admin can see all)
    if current_user.role == "patient" and current_user.id != patient_id:
         # Check if the user is actually the patient they are requesting
         # (If your patient_id logic is different, adjust this check)
         # For now, assuming strict ID match:
         raise HTTPException(status_code=403, detail="Access denied")

    # 2. Fetch with Eager Loading (The FIX)
    stmt = (
        select(RecentDoctor)
        .where(RecentDoctor.patient_id == patient_id)
        .options(selectinload(RecentDoctor.doctor))  # <--- CRITICAL FIX
        .order_by(RecentDoctor.last_visit_at.desc())
    )
    
    result = await db.execute(stmt)
    records = result.scalars().all()
    
    # 3. Format Response
    response_data = []
    
    from app.core.security import pii_encryption
    
    for r in records:
        # Decrypt doctor name
        try:
            doc_name = pii_encryption.decrypt(r.doctor.full_name)
        except:
            doc_name = "Unknown Doctor"

        response_data.append(RecentDoctorResponse(
            id=r.id,
            doctor_id=r.doctor_id,
            doctor_name=doc_name,
            specialty=r.doctor.specialty or "General Physician",
            avatar_url=r.doctor.avatar_url,
            last_visit_at=r.last_visit_at,
            visit_count=r.visit_count
        ))
        
    return response_data

@router.get("/{patient_id}/details", response_model=PatientDetailResponse)
async def get_patient_details_for_dashboard(
    patient_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Aggregate Patient Details for the Doctor's Dashboard.
    Fetches: Profile (Decrypted), Age, Latest Vitals, and Last Consultation.
    """
    # 1. Fetch Patient Profile (using Service to handle basic checks)
    # We could reuse PatientService, but we need raw access to join tables or just simple queries.
    stmt = select(Patient).where(Patient.id == patient_id)
    result = await db.execute(stmt)
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # 2. Fetch Latest Vitals (Blood Pressure & Heart Rate)
    # We query the HealthMetric table for the most recent entries
    vitals_stmt = (
        select(HealthMetric)
        .where(HealthMetric.patient_id == patient_id)
        .order_by(HealthMetric.recorded_at.desc())
        .limit(5) # Fetch last few to find BP and HR
    )
    vitals_result = await db.execute(vitals_stmt)
    vitals_records = vitals_result.scalars().all()
    
    latest_bp = next((v.value for v in vitals_records if v.metric_type == "blood_pressure"), None)
    latest_hr = next((v.value for v in vitals_records if v.metric_type == "heart_rate"), None)

    # 3. Fetch Last Consultation
    cons_stmt = (
        select(Consultation)
        .where(
            Consultation.patient_id == patient_id,
            Consultation.status == "completed"
        )
        .order_by(Consultation.scheduled_at.desc())
        .limit(1)
    )
    cons_result = await db.execute(cons_stmt)
    last_cons = cons_result.scalar_one_or_none()

    # 4. Decrypt & Calculate (The "UI Logic")
    from app.core.security import pii_encryption
    
    # Decrypt Basics
    try:
        decrypted_name = pii_encryption.decrypt(patient.full_name)
        decrypted_phone = pii_encryption.decrypt(patient.phone_number)
        dob_str = pii_encryption.decrypt(patient.date_of_birth)
        
        # Calculate Age
        dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    except:
        decrypted_name = "Error Decrypting"
        decrypted_phone = None
        age = 0

    # Decrypt Medical Data (Lists are stored as JSON)
    # Assuming 'allergies' and 'medications' are JSONB, they don't need decryption if not encrypted.
    # If they are encrypted strings, decrypt them. Based on your model, they are JSONB.
    
    return PatientDetailResponse(
        id=patient.id,
        mrn=patient.mrn,
        full_name=decrypted_name,
        age=age,
        gender=patient.gender,
        phone_number=decrypted_phone,
        email=patient.email, # Email usually plain or hashed in User table, but mapped here if synced
        address=patient.address,
        emergency_contact=patient.emergency_contact,
        
        medical_history=patient.medical_history, # Decrypt if this field is encrypted in your model
        allergies=patient.allergies or [],
        medications=patient.medications or [],
        
        latest_vitals={
            "bp": latest_bp or "N/A",
            "hr": latest_hr or "N/A"
        },
        last_consultation={
            "date": last_cons.scheduled_at if last_cons else None,
            "diagnosis": last_cons.diagnosis if last_cons else "No history"
        }
    )