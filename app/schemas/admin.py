from pydantic import BaseModel, HttpUrl, EmailStr
from typing import List, Optional
from datetime import datetime
from uuid import UUID


class ActivityFeedItem(BaseModel):
    """Represents one row in 'Recent Activity'"""
    id: UUID
    user_name: str
    user_avatar: Optional[str] = None
    event_description: str 
    resource_type: Optional[str] = "System"
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
    gender: Optional[str] = None
    type: str  
    # NEW FIELDS:
    organization_id: UUID
    organization_name: Optional[str] = None

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

class AdminAccountUpdate(BaseModel):
    """Payload for editing a user account via Admin Dashboard"""
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None  # "active" or "inactive"
    phone_number: Optional[str] = None
    specialty: Optional[str] = None
    license_number: Optional[str] = None
    department: Optional[str] = None
    organization_display_name: Optional[str] = None
    gender: Optional[str] = None
    password: Optional[str] = None
    
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
        
class AdminClinicStatsItem(BaseModel):
    """
    Statistics for the Clinic Management table.
    """
    organization_id: UUID
    organization_name: str
    active_staff_count: int
    total_patient_count: int

    class Config:
        from_attributes = True
        
class AdminProfileSchema(BaseModel):
    """Admin's own profile information"""
    name: str # display name
    full_name: Optional[str] = None # fallback
    email: str
    avatar_url: Optional[str] = None
    gender: Optional[str] = None
    phone: Optional[str] = None # fallback
    phone_number: Optional[str] = None

class OrganizationSchema(BaseModel):
    """Hospital organization details"""
    name: str
    org_email: Optional[str] = None
    timezone: Optional[str] = "UTC"
    date_format: Optional[str] = "DD/MM/YYYY"

class AllSettingsResponse(BaseModel):
    """Loads all settings forms at once (UPDATED)"""
    profile: AdminProfileSchema
    organization: OrganizationSchema
    integrations: List[dict]
    developer: dict
    backup: dict 

class AdminProfileUpdate(BaseModel):
    """Payload for updating admin's own profile"""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    phone_number: Optional[str] = None


class AuditLogItem(BaseModel):
    """Detailed audit log row for security monitoring"""
    id: UUID
    timestamp: datetime
    user_name: str
    action: str
    resource_type: str
    ip_address: Optional[str] = None
    severity: str = "info" # info, warning, critical

class AuditInsights(BaseModel):
    """Security summary for the admin audit page"""
    total_events_24h: int
    new_users_24h: int
    new_doctors_24h: int
    new_hospitals_24h: int

class AdminAuditResponse(BaseModel):
    """Composite response for the enhanced audit page"""
    logs: List[AuditLogItem]
    insights: AuditInsights
class AdminAccountDetail(BaseModel):
    """Detailed profile data for granular admin editing"""
    id: UUID
    name: str
    email: str
    role: str
    status: str
    phone_number: Optional[str] = None
    avatar_url: Optional[str] = None
    gender: Optional[str] = None
    
    # Doctor related
    specialty: Optional[str] = None
    license_number: Optional[str] = None
    department: Optional[str] = None
    
    # Organization related
    organization_id: UUID
    organization_name: str
    
    # Audit tracking
    created_at: datetime
    last_login: Optional[datetime] = None
