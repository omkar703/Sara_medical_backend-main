
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.api.v1.websockets import manager
from app.schemas.notification import NotificationResponse

class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_notification(
        self,
        user_id: UUID,
        type: str,
        title: str,
        message: str,
        organization_id: Optional[UUID] = None,
        action_url: Optional[str] = None
    ) -> Notification:
        """Create a notification in the database and push it via WebSocket."""
        notification = Notification(
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            organization_id=organization_id,
            action_url=action_url
        )
        self.db.add(notification)
        await self.db.flush()
        
        # Prepare for real-time push
        notification_data = NotificationResponse.model_validate(notification).model_dump(mode="json")
        await manager.send_personal_message(
            {"type": "notification", "data": notification_data},
            organization_id or UUID("00000000-0000-0000-0000-000000000000"), # Fallback if org is missing
            user_id
        )
        
        return notification

    async def get_user_notifications(
        self,
        user_id: UUID,
        is_read: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Notification]:
        """Fetch notifications for a specific user."""
        query = select(Notification).where(Notification.user_id == user_id)
        if is_read is not None:
            query = query.where(Notification.is_read == is_read)
        
        query = query.order_by(Notification.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def mark_as_read(self, notification_id: UUID, user_id: UUID) -> bool:
        """Mark a specific notification as read."""
        stmt = (
            update(Notification)
            .where(Notification.id == notification_id, Notification.user_id == user_id)
            .values(is_read=True, updated_at=datetime.utcnow())
        )
        result = await self.db.execute(stmt)
        return result.rowcount > 0

    async def mark_all_read(self, user_id: UUID) -> int:
        """Mark all unread notifications for a user as read."""
        stmt = (
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read == False)
            .values(is_read=True, updated_at=datetime.utcnow())
        )
        result = await self.db.execute(stmt)
        return result.rowcount
