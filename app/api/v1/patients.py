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
from app.schemas.consultation import ConsultationListResponse
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
    current_user: User = Depends(require_role(["doctor", "hospital", "admin"])),
    organization_id: UUID = Depends(get_organization_id),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    """
    Onboard a new patient by creating both User account and Patient profile.
    Requires 'doctor', 'admin', or 'hospital' role.
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
    patient_dict = patient_in.model_dump(exclude={"password", "doctor_id"}, by_alias=False)
    
    patient = await service.create_patient(
        patient_data=patient_dict,
        organization_id=organization_id,
        created_by=current_user.id,
        patient_id=new_user.id,  # Link to User account
        primary_doctor_id=getattr(patient_in, 'doctor_id', None)
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



@router.get("/my-consultations", response_model=ConsultationListResponse)
async def get_my_consultations(
    current_user: User = Depends(get_current_active_user),
    organization_id: UUID = Depends(get_organization_id),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    """
    Patient views their own consultations.
    """
    from app.api.v1.consultations import _consultation_to_response
    
    # SECURITY: Ensure non-patients (doctors/admins) don't use this intended for patient dashboard
    if current_user.role != "patient":
        # Doctors should use the main /consultations endpoint with patient_id filter
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is reserved for patient users."
        )

    from sqlalchemy.orm import selectinload
    
    stmt = (
        select(Consultation)
        .options(selectinload(Consultation.doctor), selectinload(Consultation.patient))
        .where(
            Consultation.patient_id == current_user.id,
            Consultation.deleted_at.is_(None)
        )
        .order_by(Consultation.scheduled_at.desc())
    )
    
    result = await db.execute(stmt)
    consultations = result.scalars().all()
    
    response_list = []
    for c in consultations:
        response_list.append(await _consultation_to_response(c))
        
    return ConsultationListResponse(
        consultations=response_list,
        total=len(response_list)
    )


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: UUID,
    current_user: User = Depends(require_role(["patient", "doctor", "hospital", "admin"])),
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
    # SECURITY FIX: Ensure patients can only view their own vitals
    if current_user.role == "patient" and current_user.id != patient_id:
        raise HTTPException(status_code=403, detail="Access denied: You can only view your own health metrics.")

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
        .limit(50) # Fetch more to reliably find all types
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
    import json

    def try_decrypt(value):
        """Attempt to decrypt a value; if it looks like JSON, parse it.
        If decryption fails, return the original value (best-effort non-destructive)."""
        if value is None:
            return None
        try:
            decrypted = pii_encryption.decrypt(value)
            if isinstance(decrypted, str):
                s = decrypted.strip()
                if s.startswith("{") or s.startswith("["):
                    try:
                        return json.loads(decrypted)
                    except Exception:
                        return decrypted
            return decrypted
        except Exception:
            return value

    # Decrypt Basics
    decrypted_name = try_decrypt(patient.full_name)
    decrypted_phone = try_decrypt(patient.phone_number)
    decrypted_home_phone = try_decrypt(patient.home_phone)
    dob_str = try_decrypt(patient.date_of_birth)

    # Calculate Age
    try:
        if dob_str:
            dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        else:
            age = 0
    except Exception:
        age = 0

    # Decrypt other PII / medical fields (best-effort)
    decrypted_email = try_decrypt(patient.email)
    decrypted_address = try_decrypt(patient.address)
    decrypted_emergency_contact = try_decrypt(patient.emergency_contact)
    decrypted_medical_history = try_decrypt(patient.medical_history)

    # Normalize address into fields (street, city, state, postal_code, full)
    def parse_address(addr):
        if addr is None:
            return {
                "full": None,
                "street": None,
                "city": None,
                "state": None,
                "postal_code": None,
            }

        # If already a dict-like structure, attempt to decrypt each field
        if isinstance(addr, dict):
            def _get_dec(k, alt=None):
                v = addr.get(k, None)
                if v is None and alt:
                    v = addr.get(alt, None)
                return try_decrypt(v) if v is not None else None

            full = _get_dec("full", "formatted")
            street = _get_dec("street", "address_line")
            city = _get_dec("city")
            state = _get_dec("state")
            postal = _get_dec("postal_code", "zip")

            return {
                "full": full,
                "street": street,
                "city": city,
                "state": state,
                "postal_code": postal,
            }

        # If a string: try to decrypt first, then parse JSON or comma-separated
        if isinstance(addr, str):
            # try to decrypt the string value
            decrypted_addr = try_decrypt(addr)
            # If decryption produced a dict, recurse
            if isinstance(decrypted_addr, dict):
                return parse_address(decrypted_addr)
            # If decryption produced a list, try to use first element if dict-like
            if isinstance(decrypted_addr, list) and decrypted_addr:
                first = decrypted_addr[0]
                if isinstance(first, dict):
                    return parse_address(first)
            # If decrypted string looks like JSON, parse
            if isinstance(decrypted_addr, str):
                s = decrypted_addr.strip()
                if s.startswith("{") or s.startswith("["):
                    try:
                        parsed = json.loads(s)
                        if isinstance(parsed, dict):
                            return parse_address(parsed)
                        if isinstance(parsed, list) and parsed:
                            if isinstance(parsed[0], dict):
                                return parse_address(parsed[0])
                    except Exception:
                        pass
                # fallback: treat decrypted string as comma-separated address
                parts = [p.strip() for p in decrypted_addr.split(",") if p.strip()]
            else:
                # decrypted_addr may be non-str (e.g. numeric) -> stringify fallback
                parts = [str(decrypted_addr)]

            street = parts[0] if len(parts) > 0 else None
            city = parts[1] if len(parts) > 1 else None
            state = parts[2] if len(parts) > 2 else None
            postal = parts[3] if len(parts) > 3 else None
            return {
                "full": decrypted_addr if isinstance(decrypted_addr, str) else str(decrypted_addr),
                "street": street,
                "city": city,
                "state": state,
                "postal_code": postal,
            }

        # Fallback for other types
        return {
            "full": str(addr),
            "street": None,
            "city": None,
            "state": None,
            "postal_code": None,
        }

    address_components = parse_address(decrypted_address)

    # Allergies / medications might already be lists (JSONB) or encrypted strings
    def normalize_list_field(field):
        if field is None:
            return []
        result = []

        # If field is a list/tuple, decrypt each item
        if isinstance(field, (list, tuple)):
            for item in field:
                d = try_decrypt(item)
                # if decrypted item is a list/dict, try to normalize further
                if isinstance(d, list):
                    for sub in d:
                        result.append(sub)
                elif isinstance(d, dict):
                    result.append(d)
                elif isinstance(d, str):
                    s = d.strip()
                    if s.startswith("[") or s.startswith("{"):
                        try:
                            parsed = json.loads(s)
                            if isinstance(parsed, list):
                                result.extend(parsed)
                            else:
                                result.append(parsed)
                        except Exception:
                            result.append(d)
                    else:
                        # comma separated inside an item
                        result.extend([it.strip() for it in d.split(",") if it.strip()])
                else:
                    result.append(d)
            return result

        # If field is not a list: try decrypt + parse
        decrypted = try_decrypt(field)
        if isinstance(decrypted, (list, tuple)):
            return normalize_list_field(list(decrypted))
        if isinstance(decrypted, str):
            s = decrypted.strip()
            if s.startswith("[") or s.startswith("{"):
                try:
                    parsed = json.loads(s)
                    if isinstance(parsed, list):
                        return parsed
                    return [parsed]
                except Exception:
                    return [decrypted]
            return [item.strip() for item in decrypted.split(",") if item.strip()]
        return [decrypted]
    
    allergies = normalize_list_field(patient.allergies)
    medications = normalize_list_field(patient.medications)
    
    # Decrypt last consultation fields if present
    last_cons_date = None
    last_cons_diagnosis = "No history"
    if last_cons:
        last_cons_date = last_cons.scheduled_at
        last_cons_diagnosis = try_decrypt(last_cons.diagnosis) or last_cons.diagnosis or "No history"

    # latest_vitals keep as-is (not encrypted), fallbacks handled below
    return PatientDetailResponse(
        id=patient.id,
        mrn=patient.mrn,
        full_name=decrypted_name or "Unknown",
        age=age,
        gender=try_decrypt(patient.gender) or patient.gender,
        phone_number=decrypted_phone,
        home_phone=decrypted_home_phone,
        email=decrypted_email,
        address=address_components,  # structured decrypted address
        emergency_contact=decrypted_emergency_contact,

        medical_history=decrypted_medical_history or patient.medical_history,
        allergies=allergies,
        medications=medications,

        latest_vitals={
            "bp": next((v.value for v in vitals_records if v.metric_type.strip().lower() in ["blood_pressure", "blood pressure"]), "N/A"),
            "hr": next((v.value for v in vitals_records if v.metric_type.strip().lower() in ["heart_rate", "heart rate"]), "N/A"),
            "weight": next((v.value for v in vitals_records if v.metric_type.strip().lower() == "weight"), "N/A"),
            "temp": next((v.value for v in vitals_records if v.metric_type.strip().lower() == "temperature"), "N/A"),
            "resp": next((v.value for v in vitals_records if v.metric_type.strip().lower() == "respiratory_rate"), "N/A"),
            "spo2": next((v.value for v in vitals_records if v.metric_type.strip().lower() == "oxygen_saturation"), "N/A")
        },
        health_metrics=vitals_records,
        last_consultation={
            "date": last_cons_date,
            "diagnosis": last_cons_diagnosis
        }
    )