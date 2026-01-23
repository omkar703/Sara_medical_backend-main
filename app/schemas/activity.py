from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field

class ActivityItem(BaseModel):
    activity_type: str
    description: Optional[str] = None
    status: Optional[str] = None
    created_at: datetime
    extra_data: Optional[Any] = None

    class Config:
        orm_mode = True
