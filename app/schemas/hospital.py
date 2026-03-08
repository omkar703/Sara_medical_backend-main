from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr

class DashboardMetrics(BaseModel):
    totalDoctors: int
    todayAppointments: int

class RecentActivity(BaseModel):
    activityId: str
    activityType: str
    subject: str
    status: str
    timestamp: datetime

class HospitalOverviewResponse(BaseModel):
    metrics: DashboardMetrics
    recentActivities: List[RecentActivity]
    
class DoctorDirectoryItem(BaseModel):
    id: str
    name: str
    email: str
    specialty: Optional[str] = None
    department: Optional[str] = None
    department_role: Optional[str] = None
    phone: Optional[str] = None
    joinedAt: datetime

class PatientDirectoryItem(BaseModel):
    id: str
    name: str
    mrn: str
    gender: Optional[str] = None
    dateOfBirth: Optional[str] = None
    joinedAt: datetime

class HospitalDirectoryResponse(BaseModel):
    doctors: List[DoctorDirectoryItem]
    patients: List[PatientDirectoryItem]

class PatientMetrics(BaseModel):
    activePatients: int
    patientsToday: int
    pendingPatients: int

class PatientTableItem(BaseModel):
    id: str
    mrn: str
    name: str
    gender: Optional[str] = None
    lastVisit: Optional[str] = None

class HospitalPatientsResponse(BaseModel):
    metrics: PatientMetrics
    patients: List[PatientTableItem]

class StaffMetrics(BaseModel):
    totalStaff: int

class StaffTableItem(BaseModel):
    id: str
    name: str
    role: str
    specialty: Optional[str] = None
    email: str
    phone: Optional[str] = None
    status: str

class HospitalStaffResponse(BaseModel):
    metrics: StaffMetrics
    staff: List[StaffTableItem]
    
class DoctorCreateRequest(BaseModel):
    """Schema for creating a doctor directly from the hospital dashboard"""
    email: EmailStr
    password: str
    name: str
    department: str
    department_role: str
    license_number: str

class DoctorCreateResponse(BaseModel):
    """Response schema after attempting to create a doctor"""
    message: str
    doctor_id: Optional[str] = None
    
class DoctorUpdateRequest(BaseModel):
    """Schema for updating an existing doctor's details"""
    name: Optional[str] = None
    department: Optional[str] = None
    department_role: Optional[str] = None
    specialty: Optional[str] = None
    license_number: Optional[str] = None

class DoctorUpdateResponse(BaseModel):
    """Response schema after attempting to update a doctor"""
    message: str
    doctor_id: str
    
class HealthMetricItem(BaseModel):
    id: str
    metric_type: str
    value: str
    unit: Optional[str] = None
    recorded_at: datetime
    notes: Optional[str] = None

class DocumentItem(BaseModel):
    id: str
    file_name: str
    file_type: str
    file_size: int
    category: Optional[str] = None
    uploaded_at: datetime
    status: Optional[str] = None

class PatientInfo(BaseModel):
    id: str
    full_name: str
    mrn: str
    gender: Optional[str] = None
    age: Optional[int | str] = None
    date_of_birth: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None

class PatientRecordsResponse(BaseModel):
    patient_info: PatientInfo
    health_metrics: List[HealthMetricItem]
    documents: List[DocumentItem]