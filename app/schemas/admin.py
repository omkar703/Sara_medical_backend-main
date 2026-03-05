from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from datetime import datetime
from uuid import UUID


class ActivityFeedItem(BaseModel):
    """Represents one row in 'Recent Activity'"""
    id: UUID
    user_name: str
    user_avatar: Optional[str] = None
    event_description: str 
    timestamp: datetime
    status: str

    class Config:
        from_attributes = True

class SystemAlert(BaseModel):
    """Represents an item in the 'Alerts' card"""
    id: str
    title: str
    message: str
    time_ago: str 
    severity: str = "info" 
    
class StorageStats(BaseModel):
    used_gb: float
    total_gb: float
    percentage: float
    files_count: int

class AdminOverviewResponse(BaseModel):
    """Composite response for the main admin landing page"""
    recent_activity: List[ActivityFeedItem]
    alerts: List[SystemAlert]
    storage: StorageStats
    quick_actions: List[str] 
    appointments_today: int
    total_doctors: int

class AdminInvitationItem(BaseModel):
    """Schema for the Global Invitations list"""
    id: UUID
    email: str
    role: str
    status: str
    organization_id: UUID
    expires_at: datetime
    created_at: datetime

class AdminOrgAppointmentItem(BaseModel):
    """Schema for Organization-specific Appointments"""
    id: UUID
    doctor_id: UUID
    patient_id: UUID
    requested_date: datetime
    reason: Optional[str] = None
    status: str
    doctor_name: str
    patient_name: str
    created_at: datetime

class OrgSettingsUpdate(BaseModel):
    """For the 'Organization Settings' form"""
    name: Optional[str] = None
    org_email: Optional[str] = None
    timezone: Optional[str] = None
    date_format: Optional[str] = None

class DeveloperSettingsUpdate(BaseModel):
    """For the 'API & Webhooks' form"""
    api_key_name: Optional[str] = None
    webhook_url: Optional[HttpUrl] = None

class BackupSettingsUpdate(BaseModel):
    """For the 'Backup & Security' form"""
    backup_frequency: Optional[str] = None

class AllSettingsResponse(BaseModel):
    """Loads all settings forms at once"""
    organization: dict 
    integrations: List[dict]
    developer: dict
    backup: dict 


class AccountListItem(BaseModel):
    """
    Row for the 'Account Management' table.
    """
    id: UUID
    name: str         
    email: str
    role: str          
    status: str        
    last_login: Optional[str] = None 
    avatar_url: Optional[str] = None
    type: str          

class InviteRequest(BaseModel):
    """Payload for 'Invite Team Members' """
    full_name: str     
    email: str
    role: str         
    
class DashboardAlert(BaseModel):
    id: str
    severity: str  # e.g., "high", "medium", "info"
    message: str
    created_at: datetime

class RecentActivity(BaseModel):
    id: UUID
    user: str
    action: str
    timestamp: datetime
    status: str

class DoctorApptItem(BaseModel):
    id: UUID
    patientName: str
    time: str
    status: str

class DoctorPatientItem(BaseModel):
    id: UUID
    name: str
    condition: str
    lastVisit: str

class DoctorStats(BaseModel):
    totalPatients: int
    consultations: int
    rating: float

class AdminDoctorDetailResponse(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    email: str
    specialty: str
    status: str
    phone: Optional[str] = None
    license: Optional[str] = None
    joinedDate: str
    stats: DoctorStats
    appointments: List[DoctorApptItem]
    patients: List[DoctorPatientItem]

class AccountListItem(BaseModel):
    """
    Row for the 'Account Management' table (UPDATED).
    """
    id: UUID
    name: str         
    email: str
    role: str          
    status: str        
    last_login: Optional[str] = None 
    avatar_url: Optional[str] = None
    type: str  
    # NEW FIELDS:
    organization_id: UUID
    organization_name: Optional[str] = None

class AdminAccountUpdate(BaseModel):
    """Payload for editing a user account via Admin Dashboard"""
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None  # "active" or "inactive"
    
class AdminGlobalAppointmentItem(BaseModel):
    """
    Descriptive row for the 'All Appointments' global dump.
    """
    id: UUID
    requested_date: datetime
    status: str
    reason: Optional[str] = None
    doctor_name: str
    patient_name: str
    organization_name: str
    created_at: datetime

    class Config:
        from_attributes = True