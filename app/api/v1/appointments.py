
from typing import List
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.appointment import Appointment
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentResponse,
    AppointmentStatusUpdate
)

router = APIRouter(prefix="/appointments", tags=["Appointments"])

@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    appointment_in: AppointmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Patient creates an appointment request.
    """
    appointment = Appointment(
        doctor_id=appointment_in.doctor_id,
        patient_id=current_user.id,
        requested_date=appointment_in.requested_date,
        reason=appointment_in.reason,
        status="pending"
    )
    
    db.add(appointment)
    await db.commit()
    await db.refresh(appointment)
    
    return appointment

@router.get("/patient-appointments", response_model=List[AppointmentResponse])
async def get_patient_appointments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Patient views their own appointments.
    """
    query = select(Appointment).where(
        Appointment.patient_id == current_user.id
    ).order_by(Appointment.requested_date.desc())
    
    result = await db.execute(query)
    appointments = result.scalars().all()
    return appointments

@router.patch("/{appointment_id}/status", response_model=AppointmentResponse)
async def update_appointment_status(
    appointment_id: UUID,
    status_update: AppointmentStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Doctor accepts or declines an appointment.
    """
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can update appointment status")
    
    query = select(Appointment).where(
        Appointment.id == appointment_id,
        Appointment.doctor_id == current_user.id
    )
    result = await db.execute(query)
    appointment = result.scalar_one_or_none()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    appointment.status = status_update.status
    if status_update.doctor_notes:
        appointment.doctor_notes = status_update.doctor_notes
    appointment.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(appointment)
    
    return appointment
