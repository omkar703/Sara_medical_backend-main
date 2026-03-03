"""AI Chat Service - Handles RAG (Retrieval Augmented Generation) and Chat Logic"""

import json
from typing import List, AsyncGenerator
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.chunk import Chunk
from app.models.document import Document
from app.models.consultation import Consultation
from app.models.data_access_grant import DataAccessGrant
from app.models.chat_history import ChatHistory
from app.services.aws_service import aws_service
from app.models.user import User
import uuid


class AIChatService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Private Helpers ────────────────────────────────────────────────────────

    async def _fetch_chunk_context(self, patient_id: UUID, document_id: UUID = None) -> tuple:
        """Fetch document chunks. Returns (chunks list, formatted context string)."""
        chunks = []

        if document_id:
            stmt = (
                select(Chunk)
                .where(Chunk.document_id == document_id)
                .order_by(Chunk.page_number.asc())
                .limit(10)
            )
            result = await self.db.execute(stmt)
            chunks = result.scalars().all()

        if not chunks:
            stmt = (
                select(Chunk)
                .where(Chunk.patient_id == patient_id)
                .order_by(Chunk.created_at.desc())
                .limit(10)
            )
            result = await self.db.execute(stmt)
            chunks = result.scalars().all()

        print(f"[AIChatService] Found {len(chunks)} document chunks.")

        if chunks:
            parts = [
                f"[Source: {c.source}, Page {c.page_number or 'N/A'}]\n{c.content}"
                for c in chunks
            ]
            return chunks, "\n\n---\n\n".join(parts)

        return chunks, ""

    async def _fetch_soap_context(self, patient_id: UUID) -> str:
        """
        Fetch completed SOAP notes for the patient from past consultations.
        Returns a formatted string, or empty string if none found.
        """
        stmt = (
            select(Consultation)
            .where(
                and_(
                    Consultation.patient_id == patient_id,
                    Consultation.ai_status == "completed",
                    Consultation.soap_note.isnot(None),
                )
            )
            .order_by(Consultation.scheduled_at.desc())
            .limit(5)  # Up to 5 most recent SOAP notes
        )
        result = await self.db.execute(stmt)
        consultations = result.scalars().all()

        print(f"[AIChatService] Found {len(consultations)} SOAP note(s) for patient.")

        if not consultations:
            return ""

        parts = []
        for c in consultations:
            date_str = c.scheduled_at.strftime("%Y-%m-%d") if c.scheduled_at else "Unknown date"
            soap = c.soap_note  # Already a dict (JSONB)
            if isinstance(soap, str):
                try:
                    soap = json.loads(soap)
                except Exception:
                    pass

            if isinstance(soap, dict):
                formatted = (
                    f"[SOAP Note — Consultation on {date_str}]\n"
                    f"Subjective : {soap.get('subjective', 'N/A')}\n"
                    f"Objective  : {soap.get('objective', 'N/A')}\n"
                    f"Assessment : {soap.get('assessment', 'N/A')}\n"
                    f"Plan       : {soap.get('plan', 'N/A')}"
                )
            else:
                formatted = f"[SOAP Note — Consultation on {date_str}]\n{soap}"

            parts.append(formatted)

        return "\n\n---\n\n".join(parts)

    # ── Main Chat Method ───────────────────────────────────────────────────────

    async def chat_with_patient_data(
        self,
        patient_id: UUID,
        query: str,
        requesting_user: User,
        document_id: UUID = None,
    ) -> AsyncGenerator[str, None]:
        """
        RAG Chat: retrieves document chunks AND completed SOAP notes for the patient,
        then passes both as structured context to AWS Bedrock (Claude).
        """

        # ── 1. Fetch both context sources ─────────────────────────────────────
        chunks, doc_context = await self._fetch_chunk_context(patient_id, document_id)
        soap_context = await self._fetch_soap_context(patient_id)

        # ── 2. Build structured context with clearly labelled sections ─────────
        context_sections = []

        if doc_context:
            context_sections.append(
                "=== MEDICAL DOCUMENTS ===\n"
                "The following text was extracted from the patient's uploaded medical files:\n\n"
                + doc_context
            )

        if soap_context:
            context_sections.append(
                "=== PAST CONSULTATION SOAP NOTES ===\n"
                "The following SOAP notes were generated from the patient's past consultations:\n\n"
                + soap_context
            )

        if context_sections:
            context_text = "\n\n".join(context_sections)
        else:
            context_text = "No medical context available for this patient."

        print(
            f"[AIChatService] Context built — "
            f"doc_chunks={len(chunks)}, soap_notes={'yes' if soap_context else 'no'}"
        )

        # ── 3. Save User Message ──────────────────────────────────────────────
        conversation_id = str(uuid.uuid4())
        user_msg = ChatHistory(
            conversation_id=conversation_id,
            patient_id=patient_id,
            doctor_id=requesting_user.id if requesting_user.role == "doctor" else None,
            document_id=document_id,
            user_type=requesting_user.role,
            role="user" if requesting_user.role == "patient" else "doctor",
            content=query,
            sources=None,
        )
        self.db.add(user_msg)
        await self.db.commit()

        # ── 4. Call Bedrock with combined context ──────────────────────────────
        messages = [{"role": "user", "content": query}]
        full_response = ""

        async for token in aws_service.generate_chat_stream(messages, context=context_text):
            full_response += token
            yield token

        # ── 5. Save AI Response ───────────────────────────────────────────────
        ai_msg = ChatHistory(
            conversation_id=conversation_id,
            patient_id=patient_id,
            doctor_id=requesting_user.id if requesting_user.role == "doctor" else None,
            document_id=document_id,
            user_type=requesting_user.role,
            role="assistant",
            content=full_response,
            sources=[str(c.id) for c in chunks],
        )
        self.db.add(ai_msg)
        await self.db.commit()
