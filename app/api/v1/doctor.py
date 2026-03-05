
from typing import List, Optional, Dict
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy import select, desc, func , cast, Date
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
from datetime import date

from app.schemas.consultation import ClinicalDashboardMetrics
from app.models.task import Task

from app.database import get_db
from app.core.deps import get_current_user, get_organization_id
from app.models.user import User
from app.models.patient import Patient
from app.models.appointment import Appointment
from app.models.consultation import Consultation
from app.schemas.appointment import AppointmentResponse
from app.schemas.doctor import DoctorProfileUpdate
from app.schemas.patient import PatientOnboard
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.recent_patients import RecentPatient
from app.schemas.recent_patients import RecentPatientResponse
from typing import List
from app.schemas.consultation import DoctorConsultationHistoryRow
from app.core.security import pii_encryption
from app.models.health_metric import HealthMetric
from app.schemas.health_metric import HealthMetricCreate, HealthMetricResponse

from sqlalchemy import cast, String, or_
import json
import re
from app.schemas.consultation import ConsultationSearchRow

router = APIRouter(prefix="/doctor", tags=["Doctor Dashboard"])

class DoctorPatientListItem(BaseModel):
    id: UUID
    name: str
    status_tag: str = Field(..., alias="statusTag")
    dob: str
    mrn: str
    last_visit: Optional[str] = Field(None, alias="lastVisit")
    problem: Optional[str] = None

    class Config:
        populate_by_name = True
        
class DoctorPatientListResponse(BaseModel):
    all_patients: List[DoctorPatientListItem]
    recent_patients: List[DoctorPatientListItem]
    

@router.get("/patients", response_model=DoctorPatientListResponse)
async def get_doctor_patients(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    organization_id: UUID = Depends(get_organization_id)
):
    """
    Retrieve all patients associated with the doctor's organization, 
    as well as a separate list of recently visited patients.
    """
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can access this directory")

    # Fetch patients and their latest completed consultation date in a single query
    lv_subquery = (
        select(Consultation.scheduled_at)
        .where(
            Consultation.patient_id == Patient.id,
            Consultation.status == "completed"
        )
        .order_by(Consultation.scheduled_at.desc())
        .limit(1)
        .correlate(Patient)
        .scalar_subquery()
    )

    query = select(Patient, lv_subquery.label("last_visit_at")).where(
        Patient.organization_id == organization_id, 
        Patient.deleted_at == None
    )
    result = await db.execute(query)
    rows = result.all()

    all_patients = []
    recent_patients_with_dates = []

    for p, last_visit_at in rows:
        # Decrypt fields
        try:
            name = pii_encryption.decrypt(p.full_name)
            dob = pii_encryption.decrypt(p.date_of_birth)
        except:
            name = "Encrypted"
            dob = "Unknown"

        last_visit_str = last_visit_at.strftime("%d/%m/%y") if last_visit_at else "No visits"

        item = DoctorPatientListItem(
            id=p.id,
            name=name,
            statusTag="Analysis Ready",
            dob=dob,
            mrn=p.mrn,
            lastVisit=last_visit_str,
            problem=p.medical_history or "General"
        )
        
        all_patients.append(item)
        
        # If the patient has a recorded visit, keep track of them for the 'recent' list
        if last_visit_at:
            recent_patients_with_dates.append((item, last_visit_at))

    # Sort the recent patients list by their actual datetime object (newest first)
    recent_patients_with_dates.sort(key=lambda x: x[1], reverse=True)
    
    # Extract just the Pydantic models (you can limit this to the top 10 if you want using [:10])
    recent_patients = [item for item, date in recent_patients_with_dates]

    # Return the combined response
    return DoctorPatientListResponse(
        all_patients=all_patients,
        recent_patients=recent_patients
    )

@router.get("/appointments", response_model=List[AppointmentResponse])
async def get_doctor_appointments(
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch appointments for the doctor."""
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Access denied")

    query = select(Appointment).where(Appointment.doctor_id == current_user.id)
    if status:
        query = query.where(Appointment.status == status)
    
    query = query.order_by(Appointment.requested_date.asc())
    
    result = await db.execute(query)
    appointments = result.scalars().all()
    return appointments

# New endpoint: upcoming appointment (schedule next)
@router.get("/schedule/next", response_model=Dict)
async def get_next_appointment(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Return the next upcoming confirmed appointment for the logged‑in doctor."""
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Access denied")

    from datetime import datetime
    now = datetime.utcnow()
    query = (
        select(Appointment)
        .where(
            Appointment.doctor_id == current_user.id,
            Appointment.status == "accepted",
            Appointment.requested_date >= now,
        )
        .order_by(Appointment.requested_date.asc())
        .limit(1)
    )
    result = await db.execute(query)
    appointment = result.scalar_one_or_none()
    if not appointment:
        raise HTTPException(status_code=404, detail="No upcoming appointment found")

    # Decrypt patient name
    from app.core.security import pii_encryption
    try:
        patient_name = pii_encryption.decrypt(appointment.patient.full_name)
    except:
        patient_name = "Encrypted"

    # Fetch last visit (previous completed consultation)
    from app.models.consultation import Consultation
    last_visit_q = (
        select(Consultation)
        .where(
            Consultation.patient_id == appointment.patient_id,
            Consultation.status == "completed",
        )
        .order_by(Consultation.scheduled_at.desc())
        .limit(1)
    )
    lv_res = await db.execute(last_visit_q)
    last_visit_obj = lv_res.scalar_one_or_none()
    last_visit = (
        last_visit_obj.scheduled_at.strftime("%d/%m/%y") if last_visit_obj else None
    )

    return {
        "appointment_id": str(appointment.id),
        "patient_name": patient_name,
        "patient_photo": "",
        "time": appointment.requested_date.strftime("%I:%M %p"),
        "visit_tags": ["Follow-Up"],
        "reason": appointment.reason,
        "last_visit": last_visit,
        "meeting_link": f"https://example.com/meet/{appointment.id}",
    }

# New endpoint: recent activity feed
@router.get("/activity", response_model=List[Dict])
async def get_activity_feed(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    organization_id: UUID = Depends(get_organization_id),
):
    """Return recent activity items for the doctor (appointments, consultations, team invites)."""
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Access denied")

    from app.models.activity_log import ActivityLog
    query = (
        select(ActivityLog)
        .where(ActivityLog.organization_id == organization_id)
        .order_by(ActivityLog.created_at.desc())
        .limit(20)
    )
    result = await db.execute(query)
    logs = result.scalars().all()
    activity_list = []
    for log in logs:
        activity_list.append({
            "activity_type": log.activity_type,
            "description": log.description,
            "status": log.status,
            "created_at": log.created_at.isoformat(),
            "extra_data": log.extra_data,
        })
    return activity_list


@router.patch("/profile", response_model=Dict)
async def update_doctor_profile(
    profile_in: DoctorProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update the doctor's profile (specialty, license)."""
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Access denied")

    if profile_in.specialty is not None:
        current_user.specialty = profile_in.specialty
    
    if profile_in.license_number is not None:
        from app.core.security import pii_encryption
        current_user.license_number = pii_encryption.encrypt(profile_in.license_number)

    await db.commit()
    await db.refresh(current_user)
    
    return {"message": "Profile updated successfully", "specialty": current_user.specialty}

@router.get("/{doctor_id}/recent-patients", response_model=List[RecentPatientResponse])
async def get_doctor_recent_patients(
    doctor_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get list of patients the doctor has visited/treated recently.
    """
    # 1. Security Check
    # Only the doctor themselves or an admin should see their patient list
    if current_user.role != "admin" and current_user.id != doctor_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # 2. Fetch with Eager Loading
    stmt = (
        select(RecentPatient)
        .where(RecentPatient.doctor_id == doctor_id)
        .options(selectinload(RecentPatient.patient)) # Load Patient details
        .order_by(RecentPatient.last_visit_at.desc())
    )
    
    result = await db.execute(stmt)
    records = result.scalars().all()
    
    # 3. Format Response
    response_data = []
    
    from app.core.security import pii_encryption
    from datetime import date
    
    for r in records:
        # Decrypt Patient Info
        try:
            name = pii_encryption.decrypt(r.patient.full_name)
            dob_str = pii_encryption.decrypt(r.patient.date_of_birth)
            
            # Calculate Age
            try:
                dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
                today = date.today()
                age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            except:
                age = 0
        except:
            name = "Unknown"
            age = 0

        response_data.append(RecentPatientResponse(
            id=r.id,
            patient_id=r.patient_id,
            full_name=name,
            mrn=r.patient.mrn,
            gender=r.patient.gender,
            age=age,
            last_visit_at=r.last_visit_at,
            visit_count=r.visit_count
        ))
        
    return response_data

@router.get("/{doctor_id}/history", response_model=List[DoctorConsultationHistoryRow])
async def get_doctor_consultation_history(
    doctor_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Fetch the consultation history for a specific Doctor.
    Shows list of patients treated by this doctor.
    """
    # 1. Security: Only the Doctor themselves (or Admin) can view their history
    if current_user.role != "admin" and current_user.id != doctor_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # 2. Query: Fetch Consultations + Join Patient details
    # We filter by doctor_id and only show past events (completed/cancelled)
    stmt = (
        select(Consultation)
        .where(
            Consultation.doctor_id == doctor_id,
            Consultation.status.in_(["completed", "cancelled", "no_show"])
        )
        .options(selectinload(Consultation.patient)) # Eager load Patient for name/MRN
        .order_by(Consultation.scheduled_at.desc())
    )
    
    result = await db.execute(stmt)
    consultations = result.scalars().all()
    
    # 3. Map & Decrypt
    history_list = []
    
    for c in consultations:
        # Decrypt Patient Name
        try:
            pat_name = pii_encryption.decrypt(c.patient.full_name)
        except:
            pat_name = "Unknown Patient"
            
        history_list.append(DoctorConsultationHistoryRow(
            id=c.id,
            scheduled_at=c.scheduled_at,
            status=c.status,
            patient_id=c.patient_id,
            patient_name=pat_name,
            patient_mrn=c.patient.mrn,
            patient_gender=c.patient.gender,
            diagnosis=c.diagnosis or "No diagnosis recorded"
        ))
        
    return history_list

@router.get("/{doctor_id}/search", response_model=List[ConsultationSearchRow])
async def search_doctor_records(
    doctor_id: UUID,
    q: str = Query(..., min_length=2, description="Search term for notes, diagnosis, or prescriptions"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Search through all consultation records (SOAP Notes, Prescriptions, Diagnosis).
    """
    # 1. Security Check
    if current_user.role != "admin" and current_user.id != doctor_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # 2. Construct Search Query
    search_term = f"%{q}%"
    
    stmt = (
        select(Consultation)
        .where(
            Consultation.doctor_id == doctor_id,
            or_(
                Consultation.diagnosis.ilike(search_term),
                Consultation.prescription.ilike(search_term),
                Consultation.notes.ilike(search_term),
                # Cast JSONB SOAP note to string for text searching
                cast(Consultation.soap_note, String).ilike(search_term) 
            )
        )
        .options(selectinload(Consultation.patient)) # Load patient for the response name
        .order_by(Consultation.scheduled_at.desc())
    )
    
    result = await db.execute(stmt)
    records = result.scalars().all()
    
    # 3. Format Response
    response = []
    from app.core.security import pii_encryption
    
    for c in records:
        try:
            pat_name = pii_encryption.decrypt(c.patient.full_name)
        except:
            pat_name = "Unknown"
            
        response.append(ConsultationSearchRow(
            id=c.id,
            scheduled_at=c.scheduled_at,
            status=c.status,
            patient_name=pat_name,
            patient_mrn=c.patient.mrn,
            diagnosis=c.diagnosis,
            prescription=c.prescription
        ))
        
    return response

@router.get("/me/dashboard", response_model=ClinicalDashboardMetrics)
async def get_doctor_dashboard_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    organization_id: UUID = Depends(get_organization_id)
):
    """
    Fetch personalized KPI metrics for the logged-in doctor's clinical dashboard.
    """
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Access denied")

    today = date.today()

    # 1. Pending Notes (Draft Ready or Needs Review)
    pending_notes_stmt = select(func.count(Consultation.id)).where(
        Consultation.doctor_id == current_user.id,
        Consultation.visit_state.in_(['Needs Review', 'Draft Ready'])
    )

    # 2. Patients Today & Scheduled Today
    patients_today_stmt = select(func.count(func.distinct(Consultation.patient_id))).where(
        Consultation.doctor_id == current_user.id,
        cast(Consultation.scheduled_at, Date) == today
    )

    # 3. Unsigned Orders (From Tasks table)
    unsigned_orders_stmt = select(func.count(Task.id)).where(
        Task.doctor_id == current_user.id,
        Task.status == 'pending'
    )

    # Execute queries concurrently
    pending_res, patients_res, orders_res = await asyncio.gather(
        db.execute(pending_notes_stmt),
        db.execute(patients_today_stmt),
        db.execute(unsigned_orders_stmt)
    )

    return ClinicalDashboardMetrics(
        pending_notes=pending_res.scalar() or 0,
        urgent_notes=3, # Stub: Could be derived by joining urgency_level
        avg_completion_minutes=4, # Stub: "4m 12s" in UI
        completion_delta_seconds=-18, # Stub: "-18s" in UI vs last week
        patients_today=patients_res.scalar() or 0,
        scheduled_today=16, # Stub based on UI "12 / 16 Scheduled"
        unsigned_orders=orders_res.scalar() or 0
    )


class DoctorProfileResponse(BaseModel):
    id: UUID
    full_name: str
    email: str
    role: str
    specialty: Optional[str] = None
    license_number: Optional[str] = None
    organization_id: Optional[UUID] = None
    avatar_url: Optional[str] = None
    
    class Config:
        from_attributes = True

@router.get("/me", response_model=DoctorProfileResponse)
@router.get("/me", response_model=DoctorProfileResponse)
async def get_doctor_me(
    current_user: User = Depends(get_current_user)
):
    """Get the currently logged-in doctor's own full profile."""
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Access denied")
        
    full_name = current_user.full_name
    license_no = current_user.license_number
    
    from app.core.security import pii_encryption
    try:
        full_name = pii_encryption.decrypt(current_user.full_name)
    except:
        pass
        
    if current_user.license_number:
        try:
            license_no = pii_encryption.decrypt(current_user.license_number)
        except:
            pass

    # Generate the temporary 15-minute VIP pass for the avatar
    avatar_link = None
    if current_user.avatar_url:
        from app.services.minio_service import minio_service
        from app.config import settings
        avatar_link = minio_service.generate_presigned_url(
            bucket_name=settings.MINIO_BUCKET_AVATARS,
            object_name=current_user.avatar_url
        )

    return DoctorProfileResponse(
        id=current_user.id,
        full_name=full_name,
        email=current_user.email,
        role=current_user.role,
        specialty=current_user.specialty,
        license_number=license_no,
        organization_id=current_user.organization_id,
        avatar_url=avatar_link  # Include the generated link
    )


from app.schemas.patient import PatientDetailResponse, PatientUpdate

@router.get("/patients/{patient_id}", response_model=PatientDetailResponse)
async def get_single_patient(
    patient_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    organization_id: UUID = Depends(get_organization_id)
):
    """Get a single patient's profile as a doctor."""
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Access denied")
        
    query = select(Patient).where(
        Patient.id == patient_id,
        Patient.organization_id == organization_id,
        Patient.deleted_at == None
    )
    result = await db.execute(query)
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
        
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
        # Parse if it came back as a string
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
        # Parse if it came back as a string
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

    # 5. Fetch Avatar URL from the User table
    # Since Patient ID == User ID, we can look them up directly
    user_query = select(User).where(User.id == patient.id)
    user_result = await db.execute(user_query)
    patient_user = user_result.scalar_one_or_none()

    avatar_link = None
    if patient_user and patient_user.avatar_url:
        from app.services.minio_service import minio_service
        from app.config import settings
        avatar_link = minio_service.generate_presigned_url(
            bucket_name=settings.MINIO_BUCKET_AVATARS,
            object_name=patient_user.avatar_url
        )

    return PatientDetailResponse(
        id=patient.id,
        mrn=patient.mrn,
        full_name=full_name,
        age=age,
        date_of_birth=dob_str,
        gender=patient.gender,
        avatar_url=avatar_link,  # Send the generated link to the frontend
        phone_number=phone,
        email=email,
        address=address_dict,
        emergency_contact=emergency_contact_dict,
        medical_history=medical_history,
        allergies=allergies_list,
        medications=medications_list,
        latest_vitals=None,
        last_consultation=last_consultation
    )

@router.put("/patients/{patient_id}", response_model=Dict)
async def update_patient_details(
    patient_id: UUID,
    patient_in: PatientUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    organization_id: UUID = Depends(get_organization_id)
):
    """Update a patient's details as a doctor."""
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Access denied")
        
    query = select(Patient).where(
        Patient.id == patient_id,
        Patient.organization_id == organization_id,
        Patient.deleted_at == None
    )
    result = await db.execute(query)
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
        
    # Convert the Pydantic model to a dict, excluding fields the user didn't send
    update_data = patient_in.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        # Handle explicitly nulling out a field
        if value is None:
            if hasattr(patient, field):
                setattr(patient, field, None)
            continue

        # Encrypt standard string/date fields
        if field == "full_name":
            patient.full_name = pii_encryption.encrypt(value)
        elif field == "date_of_birth":
            patient.date_of_birth = pii_encryption.encrypt(value.strftime("%Y-%m-%d"))
        elif field == "phone_number":
            patient.phone_number = pii_encryption.encrypt(value)
        elif field == "email":
            patient.email = pii_encryption.encrypt(value)
        elif field == "medical_history":
            patient.medical_history = pii_encryption.encrypt(value)
            
        # Encrypt JSON Dictionary fields
        elif field == "address" and isinstance(value, dict):
            patient.address = {
                k: pii_encryption.encrypt(str(v)) if v else v 
                for k, v in value.items()
            }

        elif field == "emergency_contact" and isinstance(value, dict):
            patient.emergency_contact = {
                k: pii_encryption.encrypt(str(v)) if v else v
                for k, v in value.items()
            }
            
        # Encrypt Array fields
        elif field == "allergies" and isinstance(value, list):
            patient.allergies = [pii_encryption.encrypt(str(item)) for item in value]
        elif field == "medications" and isinstance(value, list):
            patient.medications = [pii_encryption.encrypt(str(item)) for item in value]
            
        # Handle unencrypted fields (like gender)
        elif hasattr(patient, field):
            setattr(patient, field, value)
            
    patient.updated_at = datetime.utcnow()
    await db.commit()
    
    return {"message": "Patient updated successfully"}

@router.post("/patients/{patient_id}/health", response_model=HealthMetricResponse)
async def add_patient_health_metric(
    patient_id: UUID,
    metric_in: HealthMetricCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    organization_id: UUID = Depends(get_organization_id)
):
    """Add a new health metric (vital sign) for a patient."""
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Access denied")
        
    # Verify patient exists and belongs to the doctor's organization
    query = select(Patient).where(
        Patient.id == patient_id,
        Patient.organization_id == organization_id,
        Patient.deleted_at == None
    )
    result = await db.execute(query)
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
        
    # Add new metric
    new_metric = HealthMetric(
        patient_id=patient.id,
        metric_type=metric_in.metric_type,
        value=metric_in.value,
        unit=metric_in.unit,
        notes=metric_in.notes,
        recorded_at=metric_in.recorded_at
    )
    
    db.add(new_metric)
    await db.commit()
    await db.refresh(new_metric)
    
    return new_metric


@router.put("/patients/{patient_id}/health/{metric_id}", response_model=HealthMetricResponse)
async def edit_patient_health_metric(
    patient_id: UUID,
    metric_id: UUID,
    metric_in: HealthMetricCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    organization_id: UUID = Depends(get_organization_id)
):
    """Edit an existing health metric for a patient (e.g. fixing a typo)."""
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Access denied")
        
    # Verify the specific metric exists and belongs to the patient
    query = select(HealthMetric).where(
        HealthMetric.id == metric_id,
        HealthMetric.patient_id == patient_id
    )
    result = await db.execute(query)
    metric = result.scalar_one_or_none()
    
    if not metric:
        raise HTTPException(status_code=404, detail="Health metric not found")
        
    # Update fields
    metric.metric_type = metric_in.metric_type
    metric.value = metric_in.value
    metric.unit = metric_in.unit
    metric.notes = metric_in.notes
    metric.recorded_at = metric_in.recorded_at
    
    await db.commit()
    await db.refresh(metric)
    
    return metric
@router.post("/extract-credentials", status_code=status.HTTP_200_OK)
async def extract_credentials(
    certificate_image: UploadFile = File(...)
):
    """
    Extract doctor credentials from an uploaded certificate image using Vision LLM.
    """
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/webp"]
    if certificate_image.content_type not in allowed_types:
        return JSONResponse(
            status_code=400,
            content={"error": "Unsupported file format. Allowed formats: JPG, JPEG, PNG, WEBP"}
        )
        
    file_bytes = await certificate_image.read()
    if len(file_bytes) > 10 * 1024 * 1024:
        return JSONResponse(
            status_code=400,
            content={"error": "File too large. Max size is 10MB."}
        )
        
    from app.services.aws_service import AWSService
    aws = AWSService()
    result = await aws.extract_credentials_from_image(file_bytes, certificate_image.content_type)
    
    if not result:
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to extract credentials from image."}
        )
        
    return result
