from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

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