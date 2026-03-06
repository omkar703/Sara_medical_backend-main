"""Notifications API — fetch, mark-read, and approve/reject AI access grants from notifications."""

from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.notification import Notification
from app.models.data_access_grant import DataAccessGrant
from app.schemas.notification import NotificationResponse
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


# ──────────────────────────────────────────────
# Standard notification endpoints
# ──────────────────────────────────────────────

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


# ──────────────────────────────────────────────
# AI Access Grant — Approve / Reject via Notification
# ──────────────────────────────────────────────

@router.post(
    "/{notification_id}/approve-ai-access",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Patient approves an AI access request from a notification",
    description=(
        "The patient calls this endpoint after receiving an `access_requested` notification. "
        "It activates the linked `DataAccessGrant` so the doctor gains AI access to the "
        "patient's medical records. Marks the notification as read and sends the doctor "
        "a real-time notification about the approval."
    )
)
async def approve_ai_access_from_notification(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Patient approves a pending AI access request that came in via a notification.

    - Only the **patient** who owns the notification may call this.
    - The notification must be of type `access_requested` and must have a `grant_id`.
    - The linked `DataAccessGrant` is set to `status=active`, `ai_access_permission=True`.
    - A notification is sent to the **doctor** confirming approval.
    """
    if current_user.role != "patient":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only patients can approve AI access requests."
        )

    # 1. Fetch and validate the notification
    notif_result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id
        )
    )
    notification = notif_result.scalars().first()

    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")

    if notification.type != "access_requested":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This notification is not an AI access request."
        )

    if not notification.grant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Notification has no linked access grant. Cannot approve."
        )

    # 2. Fetch the linked DataAccessGrant
    grant_result = await db.execute(
        select(DataAccessGrant).where(
            DataAccessGrant.id == notification.grant_id,
            DataAccessGrant.patient_id == current_user.id
        )
    )
    grant = grant_result.scalars().first()

    if not grant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Access grant not found or does not belong to you."
        )

    if grant.status == "active" and grant.is_active:
        # Already approved — idempotent
        await _mark_notification_read(db, notification)
        await db.commit()
        return {"status": "already_approved", "message": "Access was already active.", "grant_id": str(grant.id)}

    if grant.status == "revoked":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This access grant has been revoked and cannot be approved."
        )

    # 3. Approve: flip the grant to active
    grant.status = "active"
    grant.is_active = True
    grant.ai_access_permission = True
    grant.revoked_at = None

    # 4. Mark notification as read
    await _mark_notification_read(db, notification)

    # 5. Notify the doctor — real-time push + DB record
    ns = NotificationService(db)
    await ns.create_notification(
        user_id=grant.doctor_id,
        type="access_approved",
        title="AI Access Approved",
        message=(
            "The patient has approved your request to use AI to analyze their medical records. "
            "You can now start an AI chat session for this patient."
        ),
        action_url="/patients",
        action_metadata={
            "patient_id": str(current_user.id),
            "grant_id": str(grant.id)
        }
    )

    # 6. Audit log
    from app.services.audit_service import AuditService
    audit = AuditService(db)
    await audit.log_event(
        user_id=current_user.id,
        action="permission.approve",
        resource_type="data_access_grant",
        resource_id=grant.id,
        organization_id=current_user.organization_id,
        metadata={"doctor_id": str(grant.doctor_id), "ai_access": True}
    )

    await db.commit()

    return {
        "status": "approved",
        "message": "AI access approved. The doctor has been notified.",
        "grant_id": str(grant.id),
        "doctor_id": str(grant.doctor_id)
    }


@router.post(
    "/{notification_id}/reject-ai-access",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Patient rejects an AI access request from a notification",
    description=(
        "The patient calls this endpoint to reject a pending AI access request from "
        "a notification. The linked `DataAccessGrant` is set to `status=rejected`. "
        "The doctor receives a notification about the rejection."
    )
)
async def reject_ai_access_from_notification(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Patient rejects a pending AI access request that came in via a notification.

    - Only the **patient** who owns the notification may call this.
    - The notification must be of type `access_requested` and must have a `grant_id`.
    - The linked `DataAccessGrant` is set to `status=rejected`, `is_active=False`.
    - A notification is sent to the **doctor** informing them of the rejection.
    """
    if current_user.role != "patient":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only patients can reject AI access requests."
        )

    # 1. Fetch and validate the notification
    notif_result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id
        )
    )
    notification = notif_result.scalars().first()

    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")

    if notification.type != "access_requested":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This notification is not an AI access request."
        )

    if not notification.grant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Notification has no linked access grant. Cannot reject."
        )

    # 2. Fetch the linked DataAccessGrant
    grant_result = await db.execute(
        select(DataAccessGrant).where(
            DataAccessGrant.id == notification.grant_id,
            DataAccessGrant.patient_id == current_user.id
        )
    )
    grant = grant_result.scalars().first()

    if not grant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Access grant not found or does not belong to you."
        )

    if grant.status == "revoked":
        # Already rejected/revoked — idempotent
        await _mark_notification_read(db, notification)
        await db.commit()
        return {"status": "already_rejected", "message": "Access was already rejected.", "grant_id": str(grant.id)}

    # 3. Reject: deactivate the grant
    grant.status = "revoked"
    grant.is_active = False
    grant.revoked_at = datetime.now(timezone.utc)
    grant.revoked_reason = "Patient rejected the AI access request."

    # 4. Mark notification as read
    await _mark_notification_read(db, notification)

    # 5. Notify the doctor — real-time push + DB record
    ns = NotificationService(db)
    await ns.create_notification(
        user_id=grant.doctor_id,
        type="access_rejected",
        title="AI Access Request Rejected",
        message=(
            "The patient has declined your request to use AI to analyze their medical records. "
            "You may request access again if needed."
        ),
        action_url="/patients",
        action_metadata={
            "patient_id": str(current_user.id),
            "grant_id": str(grant.id)
        }
    )

    # 6. Audit log
    from app.services.audit_service import AuditService
    audit = AuditService(db)
    await audit.log_event(
        user_id=current_user.id,
        action="permission.reject",
        resource_type="data_access_grant",
        resource_id=grant.id,
        organization_id=current_user.organization_id,
        metadata={"doctor_id": str(grant.doctor_id), "ai_access": False}
    )

    await db.commit()

    return {
        "status": "rejected",
        "message": "AI access request rejected. The doctor has been notified.",
        "grant_id": str(grant.id),
        "doctor_id": str(grant.doctor_id)
    }


# ──────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────

async def _mark_notification_read(db: AsyncSession, notification: Notification) -> None:
    """Mark a notification as read (mutates in-place, commit handled by caller)."""
    if not notification.is_read:
        notification.is_read = True
        notification.updated_at = datetime.now(timezone.utc)
