
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.notification import NotificationResponse
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("", response_model=List[NotificationResponse])
async def get_notifications(
    is_read: Optional[bool] = Query(None, description="Filter by read status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch notifications for the current user."""
    service = NotificationService(db)
    notifications = await service.get_user_notifications(
        user_id=current_user.id,
        is_read=is_read,
        limit=limit,
        offset=offset
    )
    return notifications

@router.patch("/{notification_id}/read", response_model=dict)
async def mark_notification_as_read(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark a specific notification as read."""
    service = NotificationService(db)
    success = await service.mark_as_read(notification_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found or not owned by user"
        )
    await db.commit()
    return {"status": "success", "message": "Notification marked as read"}

@router.patch("/read-all", response_model=dict)
async def mark_all_notifications_as_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark all unread notifications for the user as read."""
    service = NotificationService(db)
    count = await service.mark_all_read(current_user.id)
    await db.commit()
    return {"status": "success", "message": f"{count} notifications marked as read"}
