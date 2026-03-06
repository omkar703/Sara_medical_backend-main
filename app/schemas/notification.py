
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class NotificationBase(BaseModel):
    title: str
    message: str
    type: str
    action_url: Optional[str] = None
    organization_id: Optional[UUID] = None


class NotificationCreate(NotificationBase):
    user_id: UUID


class NotificationUpdate(BaseModel):
    is_read: Optional[bool] = None


class NotificationResponse(NotificationBase):
    id: UUID
    user_id: UUID
    is_read: bool
    created_at: datetime
    updated_at: datetime
    # For AI-access request notifications: references the pending DataAccessGrant
    grant_id: Optional[UUID] = None
    # Extra contextual data (e.g. doctor name/id) for the frontend to render action buttons
    action_metadata: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)
