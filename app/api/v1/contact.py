"""Contact Form API endpoints"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.contact import (
    ContactMessageCreate,
    ContactMessageListResponse,
    ContactMessageResponse,
    ContactMessageSuccessResponse,
)
from app.services.contact_service import ContactMessageService
from app.services.email import send_contact_form_email

router = APIRouter(prefix="/contact", tags=["Contact"])


@router.post(
    "/submit",
    response_model=ContactMessageSuccessResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_contact_form(
    contact_data: ContactMessageCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Submit a contact form message

    This endpoint accepts contact form data and:
    1. Stores the message in the database
    2. Sends an email notification to enterprise@saramedico.com

    Args:
        contact_data: Contact form data

    Returns:
        Success response with message ID
    """
    try:
        # Create contact message service
        service = ContactMessageService(db)

        # Save message to database
        message = await service.create_contact_message(contact_data)

        # Send email to enterprise email
        email_sent = await send_contact_form_email(
            sender_name=f"{contact_data.first_name} {contact_data.last_name}",
            sender_email=contact_data.email,
            sender_phone=contact_data.phone,
            subject=contact_data.subject,
            message=contact_data.message,
            to_email=settings.ENTERPRISE_EMAIL,
        )

        if not email_sent:
            # Log warning but don't fail the request - message was saved
            print(
                f"Warning: Could not send email notification for contact message {message.id}"
            )

        return ContactMessageSuccessResponse(id=message.id)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        print(f"Error submitting contact form: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit contact form. Please try again later.",
        )


@router.get(
    "/messages",
    response_model=list[ContactMessageListResponse],
)
async def get_contact_messages(
    skip: int = 0,
    limit: int = 10,
    unread_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all contact messages (Admin only)

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        unread_only: Filter to only unread messages
        current_user: Currently logged-in user

    Returns:
        List of contact messages
    """
    # Check if user is admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can view contact messages",
        )

    service = ContactMessageService(db)
    messages = await service.get_contact_messages(
        skip=skip, limit=limit, unread_only=unread_only
    )

    return messages


@router.get(
    "/messages/{message_id}",
    response_model=ContactMessageResponse,
)
async def get_contact_message(
    message_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific contact message (Admin only)

    Args:
        message_id: Contact message ID
        current_user: Currently logged-in user

    Returns:
        Contact message details
    """
    # Check if user is admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can view contact messages",
        )

    try:
        from uuid import UUID

        message_uuid = UUID(message_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid message ID format",
        )

    service = ContactMessageService(db)
    message = await service.get_contact_message_by_id(message_uuid)

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact message not found",
        )

    return message


@router.patch(
    "/messages/{message_id}/read",
    response_model=ContactMessageResponse,
)
async def mark_message_as_read(
    message_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Mark a contact message as read (Admin only)

    Args:
        message_id: Contact message ID
        current_user: Currently logged-in user

    Returns:
        Updated contact message
    """
    # Check if user is admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can manage contact messages",
        )

    try:
        from uuid import UUID

        message_uuid = UUID(message_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid message ID format",
        )

    service = ContactMessageService(db)
    message = await service.mark_as_read(message_uuid)

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact message not found",
        )

    return message


@router.delete(
    "/messages/{message_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_contact_message(
    message_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a contact message (Admin only)

    Args:
        message_id: Contact message ID
        current_user: Currently logged-in user
    """
    # Check if user is admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can delete contact messages",
        )

    try:
        from uuid import UUID

        message_uuid = UUID(message_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid message ID format",
        )

    service = ContactMessageService(db)
    deleted = await service.delete_contact_message(message_uuid)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact message not found",
        )


@router.get(
    "/stats/unread-count",
)
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get count of unread contact messages (Admin only)

    Args:
        current_user: Currently logged-in user

    Returns:
        Count of unread messages
    """
    # Check if user is admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can view statistics",
        )

    service = ContactMessageService(db)
    count = await service.get_total_unread_count()

    return {"unread_count": count}
