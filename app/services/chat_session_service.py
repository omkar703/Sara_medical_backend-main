"""Chat Session Service - Manages persistent doctor-AI chat sessions"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat_session import ChatSession, ChatMessage
from app.services.aws_service import aws_service


class ChatSessionService:
    """
    Manages creation, retrieval and updating of persistent AI chat sessions.
    Each session is scoped to a doctor–patient relationship.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Session CRUD ───────────────────────────────────────────────────────────

    async def create_session(
        self,
        doctor_id: UUID,
        patient_id: UUID,
        title: Optional[str] = None,
    ) -> ChatSession:
        """Create a new persistent chat session."""
        session = ChatSession(
            id=uuid.uuid4(),
            doctor_id=doctor_id,
            patient_id=patient_id,
            title=title or None,  # None means auto-generate on first message
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def list_sessions(
        self,
        doctor_id: UUID,
        patient_id: UUID,
    ) -> List[ChatSession]:
        """
        Return all chat sessions for a doctor–patient pair,
        ordered by most recently active (updated_at DESC).
        """
        stmt = (
            select(ChatSession)
            .where(
                and_(
                    ChatSession.doctor_id == doctor_id,
                    ChatSession.patient_id == patient_id,
                )
            )
            .order_by(ChatSession.updated_at.desc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_session(
        self,
        session_id: UUID,
        doctor_id: UUID,
    ) -> Optional[ChatSession]:
        """
        Fetch a session + its messages.
        Returns None if not found OR if it doesn't belong to the doctor.
        """
        stmt = select(ChatSession).where(
            and_(
                ChatSession.id == session_id,
                ChatSession.doctor_id == doctor_id,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_session_messages(
        self,
        session_id: UUID,
        limit: int = 50,
    ) -> List[ChatMessage]:
        """Fetch the N most recent messages from a session (for display)."""
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_session_history_for_prompt(
        self,
        session_id: UUID,
        limit: int = 10,
    ) -> List[dict]:
        """
        Fetch last N messages formatted as Claude message dicts:
        [{"role": "user"|"assistant", "content": "..."}]
        """
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        messages = result.scalars().all()

        # Reverse to chronological order for the prompt
        messages = list(reversed(messages))

        return [
            {
                "role": "user" if m.role == "doctor" else "assistant",
                "content": m.content,
            }
            for m in messages
        ]

    async def save_messages(
        self,
        session_id: UUID,
        doctor_message: str,
        ai_response: str,
        sources: Optional[List[str]] = None,
        confidence: Optional[str] = None,
    ) -> None:
        """Persist both the doctor's question and the AI's response."""
        doctor_msg = ChatMessage(
            id=uuid.uuid4(),
            session_id=session_id,
            role="doctor",
            content=doctor_message,
        )
        ai_msg = ChatMessage(
            id=uuid.uuid4(),
            session_id=session_id,
            role="assistant",
            content=ai_response,
            sources=sources,
            confidence=confidence,
        )
        self.db.add(doctor_msg)
        self.db.add(ai_msg)

        # Update session timestamp so it bubbles to top of sidebar
        await self.db.execute(
            update(ChatSession)
            .where(ChatSession.id == session_id)
            .values(updated_at=datetime.now(timezone.utc))
        )
        await self.db.commit()

    async def set_title(
        self,
        session_id: UUID,
        title: str,
    ) -> None:
        """Set the title of a session (called after auto-generation)."""
        await self.db.execute(
            update(ChatSession)
            .where(ChatSession.id == session_id)
            .values(title=title)
        )
        await self.db.commit()

    # ── Title Auto-Generation ──────────────────────────────────────────────────

    async def auto_generate_title(self, first_message: str) -> str:
        """
        Call Claude with a minimal prompt to create a concise 4–6 word session title.
        Falls back to a date-based title if Claude is unavailable.
        """
        prompt = (
            f"Generate a short, descriptive chat session title (4-6 words) "
            f"for a medical AI assistant chat that starts with this question: "
            f"\"{first_message}\"\n\n"
            f"Reply with ONLY the title, no quotes, no punctuation at the end."
        )
        try:
            title = await aws_service.generate_text(prompt)
            # Trim to 255 chars and clean up whitespace
            title = title.strip()[:255]
            if not title:
                raise ValueError("Empty title returned")
            return title
        except Exception:
            return f"Chat – {datetime.now(timezone.utc).strftime('%b %d, %Y')}"
