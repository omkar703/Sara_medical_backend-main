
from typing import List, Optional, Dict
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

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

@router.get("/patients", response_model=List[DoctorPatientListItem])
async def get_doctor_patients(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    organization_id: UUID = Depends(get_organization_id)
):
    """
    Retrieve patients associated with the doctor's organization.
    Assumes doctors see all patients in their clinic/organization.
    """
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can access this directory")

    from app.core.security import pii_encryption

    # Fetch patients in the organization
    query = select(Patient).where(Patient.organization_id == organization_id, Patient.deleted_at == None)
    result = await db.execute(query)
    patients = result.scalars().all()

    response = []
    for p in patients:
        # Decrypt fields
        try:
            name = pii_encryption.decrypt(p.full_name)
            dob = pii_encryption.decrypt(p.date_of_birth)
        except:
            name = "Encrypted"
            dob = "Unknown"

        # Fetch last visit from consultations
        visit_query = select(Consultation).where(
            Consultation.patient_id == p.id,
            Consultation.status == "completed"
        ).order_by(Consultation.scheduled_at.desc()).limit(1)
        visit_result = await db.execute(visit_query)
        last_visit_obj = visit_result.scalar_one_or_none()
        last_visit_str = last_visit_obj.scheduled_at.strftime("%d/%m/%y") if last_visit_obj else "No visits"

        response.append(DoctorPatientListItem(
            id=p.id,
            name=name,
            statusTag="Analysis Ready", # Dummy tag as seen in UI
            dob=dob,
            mrn=p.mrn,
            lastVisit=last_visit_str,
            problem=p.medical_history or "General"
        ))

    return response

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


@router.post("/onboard-patient", response_model=Dict)
async def onboard_patient(
    patient_info: PatientOnboard,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    organization_id: UUID = Depends(get_organization_id)
):
    """
    Onboard a new patient by a doctor or hospital admin.
    Creates both User and Patient records.
    """
    if current_user.role not in ["doctor", "admin", "hospital"]:
        raise HTTPException(status_code=403, detail="Only healthcare providers can onboard patients")

    from app.core.security import hash_password, PIIEncryption
    from app.models.user import User
    from app.models.patient import Patient
    from app.services.patient_service import PatientService

    # 1. Check if email already exists in User table
    email_query = select(User).where(User.email == patient_info.email.lower())
    email_result = await db.execute(email_query)
    if email_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User with this email already exists")

    # 2. Create User record
    pii_encryption = PIIEncryption()
    encrypted_name = pii_encryption.encrypt(patient_info.full_name)
    encrypted_phone = pii_encryption.encrypt(patient_info.phone_number) if patient_info.phone_number else None
    
    new_user = User(
        email=patient_info.email.lower(),
        password_hash=hash_password(patient_info.password),
        full_name=encrypted_name,
        phone_number=encrypted_phone,
        role="patient",
        organization_id=organization_id,
        email_verified=True # Auto-verify for onboarded patients
    )
    db.add(new_user)
    await db.flush() # Get user ID

    # 3. Create Patient record using PatientService
    patient_service = PatientService(db)
    
    # Prepare patient data for service
    p_data = patient_info.dict(exclude={"password"})
    
    # PatientService expects some specific formats or will handle encryption
    # Let's check PatientService.create_patient signature again or just call it
    
    await patient_service.create_patient(
        patient_data=p_data,
        organization_id=organization_id,
        created_by=current_user.id,
        patient_id=new_user.id
    )
    
    await db.commit()

    return {
        "message": "Patient onboarded successfully",
        "patient_id": str(new_user.id),
        "email": patient_info.email,
        "temporary_password": patient_info.password # In real scenario, sent via secure channel or email
    }
