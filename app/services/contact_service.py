"""Contact Message Service"""

from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact_message import ContactMessage
from app.schemas.contact import ContactMessageCreate


class ContactMessageService:
    """Service for handling contact messages"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_contact_message(self, message_data: ContactMessageCreate) -> ContactMessage:
        """
        Create a new contact message

        Args:
            message_data: Contact message data

        Returns:
            Created contact message
        """
        message = ContactMessage(
            first_name=message_data.first_name,
            last_name=message_data.last_name,
            email=message_data.email,
            phone=message_data.phone,
            subject=message_data.subject,
            message=message_data.message,
            read=False
        )

        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)

        return message

    async def get_contact_messages(
        self,
        skip: int = 0,
        limit: int = 10,
        unread_only: bool = False
    ) -> list[ContactMessage]:
        """
        Get all contact messages with optional filtering

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            unread_only: Filter to only unread messages

        Returns:
            List of contact messages
        """
        stmt = select(ContactMessage).order_by(desc(ContactMessage.created_at))

        if unread_only:
            stmt = stmt.where(ContactMessage.read.is_(False))

        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_contact_message_by_id(self, message_id: UUID) -> ContactMessage | None:
        """
        Get a contact message by ID

        Args:
            message_id: Message ID

        Returns:
            Contact message or None
        """
        result = await self.db.execute(
            select(ContactMessage).where(ContactMessage.id == message_id)
        )
        return result.scalar_one_or_none()

    async def mark_as_read(self, message_id: UUID) -> ContactMessage | None:
        """
        Mark a contact message as read

        Args:
            message_id: Message ID

        Returns:
            Updated contact message or None
        """
        message = await self.get_contact_message_by_id(message_id)
        if message:
            message.read = True
            await self.db.commit()
            await self.db.refresh(message)
        return message

    async def delete_contact_message(self, message_id: UUID) -> bool:
        """
        Delete a contact message

        Args:
            message_id: Message ID

        Returns:
            True if deleted, False otherwise
        """
        message = await self.get_contact_message_by_id(message_id)
        if message:
            await self.db.delete(message)
            await self.db.commit()
            return True
        return False

    async def get_total_unread_count(self) -> int:
        """
        Get total count of unread messages

        Returns:
            Count of unread messages
        """
        result = await self.db.execute(
            select(ContactMessage).where(ContactMessage.read.is_(False))
        )
        messages = result.scalars().all()
        return len(messages)
