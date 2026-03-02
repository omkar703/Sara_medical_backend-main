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
