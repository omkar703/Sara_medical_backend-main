"""AI Chat Service - Session-aware RAG with Medical Guardrails"""

import json
from typing import List, AsyncGenerator, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.chunk import Chunk
from app.models.document import Document
from app.models.consultation import Consultation
from app.models.user import User
from app.services.aws_service import aws_service


# ── Constants ──────────────────────────────────────────────────────────────────

MAX_CHUNKS = 5           # Top-N document chunks to pass to LLM
MAX_SOAP_NOTES = 3       # Top-N SOAP notes to include
MAX_HISTORY_MESSAGES = 10  # Last-N messages from chat session

# Confidence thresholds
HIGH_CONFIDENCE_THRESHOLD = 3   # 3+ chunks → High
LOW_CONFIDENCE_THRESHOLD = 1    # 0 chunks → skip LLM, return fallback


# ── Medical Guardrail System Prompt ───────────────────────────────────────────

MEDICAL_SYSTEM_PROMPT = """\
You are "SaraMedico Clinical Intelligence," a state-of-the-art clinical AI designed to assist licensed physicians during consultations. Your primary goal is to provide evidence-based insights derived solely from the patient's medical history.

### OPERATIONAL PRINCIPLES:
1.  **Strict Evidence Grounding**: You are a retrieval-augmented model. Every clinical statement must be directly traceable to the provided medical context (Documents or SOAP notes). If a fact is not in the context, it does not exist.
2.  **No Hallucinations**: Do not infer patient conditions, medications, or historical events. If data is missing (e.g., "Patient's current BP?"), state clearly: "Retrieved records do not specify the current blood pressure."
3.  **Clinical Nuance**: Distinguish between "History of," "Suspected," and "Confirmed" conditions as documented.
4.  **Inline Citations**: Support every clinical claim with a bracketed citation pointing to the source document or SOAP note (e.g., "[Lab_Results_03_24.pdf]" or "[SOAP Note 2024-01-10]").

### RESPONSE ARCHITECTURE (Your response MUST follow this structure):
**Clinical Overview:** (A high-level, one-sentence professional summary of the patient's relevant status)

**Evidence-Based Findings:**
- (Use bullet points for specific diagnostic, laboratory, or symptomatic facts)
- (Group findings by category like "Vital Signs" or "Past Medical History")

**Clinical Evidence Inventory:** (List of all specific files or SOAP notes consulted to generate this response)

**Synthesized Answer:** (A direct, clinical answer to the physician's query, highlighting critical alerts if present)
"""

GENERAL_MEDICAL_PROMPT = """\
You are "SaraMedico Clinical Intelligence," a state-of-the-art clinical AI designed to assist licensed physicians.
Currently, no specific patient medical records or documents were retrieved for this query.
You must answer the user's query using your general medical knowledge. 

### OPERATIONAL PRINCIPLES:
1. Clearly state that your answer is based on general medical knowledge as no patient-specific records were found in the context.
2. Provide a helpful, evidence-based, and clinically sound answer to the physician's query.

### RESPONSE ARCHITECTURE:
**General Clinical Insight:** (A direct, clinical answer to the query)
**Detailed Breakdown:** (Use bullet points for further elaboration)
"""

DOCUMENT_SPECIFIC_SYSTEM_PROMPT = """\
You are "SaraMedico Clinical Intelligence," a state-of-the-art clinical AI designed to assist licensed physicians.
You are currently analyzing a **SPECIFIC** medical document. 

### OPERATIONAL PRINCIPLES:
1.  **Strict Document Focus**: Your answer MUST be derived ONLY from the provided document chunks. Do NOT bring in external patient history (SOAP notes) or general knowledge unless specified.
2.  **No Hallucinations**: If the document content is not relevant to the user's query or doesn't contain the answer, clearly state: "The current document does not contain this information."
3.  **Cross-Document Permission**: If you believe a query could be answered better by referencing the patient's wider medical record (other documents or SOAP notes), you MUST suggest this to the doctor: "This query is complex. May I refer to other medical documents in this patient's history to provide a complete answer?" (or similar phrasing). 
4.  **Accuracy**: Describe the document type (e.g., Lab Result, Scan, Certificate) and its key findings as documented.

### RESPONSE ARCHITECTURE:
**Document Summary:** (A high-level summary of what the document is)
**Extracted Details:** (Key findings or data points from the document)
**Synthesized Answer:** (A direct answer to the user's query about this document)
"""

FALLBACK_BEDROCK_UNAVAILABLE = (
    "The AI clinical assistant is temporarily unavailable. Please try again later."
)

class AIChatService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Private Helpers ────────────────────────────────────────────────────────

    async def _fetch_chunk_context(
        self,
        patient_id: UUID,
        document_id: Optional[UUID] = None,
    ) -> tuple[List[Chunk], str]:
        """
        Fetch top MAX_CHUNKS document chunks for RAG.
        Returns (chunks list, formatted context string with source attribution).
        """
        chunks = []

        if document_id:
            stmt = (
                select(Chunk)
                .join(Document, Chunk.document_id == Document.id)
                .where(
                    and_(
                        Chunk.document_id == document_id,
                        Document.deleted_at.is_(None)
                    )
                )
                .order_by(Chunk.page_number.asc())
                .limit(MAX_CHUNKS)
            )
            result = await self.db.execute(stmt)
            chunks = result.scalars().all()

        if not chunks:
            stmt = (
                select(Chunk)
                .join(Document, Chunk.document_id == Document.id)
                .where(
                    and_(
                        Chunk.patient_id == patient_id,
                        Document.deleted_at.is_(None)
                    )
                )
                .order_by(Chunk.created_at.desc())
                .limit(MAX_CHUNKS)
            )
            result = await self.db.execute(stmt)
            chunks = result.scalars().all()

        if not chunks:
            return [], ""

        # Build context with source attribution for each chunk
        parts = []
        for c in chunks:
            # Fetch the document name for citation
            doc_stmt = select(Document.file_name).where(Document.id == c.document_id)
            doc_result = await self.db.execute(doc_stmt)
            doc_name = doc_result.scalar_one_or_none() or "Unknown Document"

            parts.append(
                f"[Source: {doc_name} | Section: {c.source} | Page: {c.page_number or 'N/A'}]\n"
                f"{c.content}"
            )

        print(f"[AIChatService] Fetched {len(chunks)} document chunks.")
        return chunks, "\n\n---\n\n".join(parts)

    async def _fetch_soap_context(self, patient_id: UUID) -> str:
        """
        Fetch completed SOAP notes (up to MAX_SOAP_NOTES most recent).
        Returns formatted string ready for inclusion in the prompt.
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
            .limit(MAX_SOAP_NOTES)
        )
        result = await self.db.execute(stmt)
        consultations = result.scalars().all()

        if not consultations:
            return ""

        parts = []
        for c in consultations:
            date_str = c.scheduled_at.strftime("%Y-%m-%d") if c.scheduled_at else "Unknown date"
            soap = c.soap_note
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

        print(f"[AIChatService] Fetched {len(consultations)} SOAP note(s).")
        return "\n\n---\n\n".join(parts)

    def _compute_confidence(self, chunk_count: int) -> str:
        """Determine confidence level based on retrieved context volume."""
        if chunk_count >= HIGH_CONFIDENCE_THRESHOLD:
            return "high"
        elif chunk_count >= LOW_CONFIDENCE_THRESHOLD:
            return "medium"
        else:
            return "low"

    # ── Main Chat Method ───────────────────────────────────────────────────────

    async def chat_with_patient_data(
        self,
        patient_id: UUID,
        query: str,
        requesting_user: User,
        document_id: Optional[UUID] = None,
        session_history: Optional[List[dict]] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Session-aware, guardrailed RAG chat.

        Context Sources (in priority order):
        1. Document chunks (RAG vector search)
        2. SOAP notes (clinical consultation summaries)
        3. Session history (conversation memory)

        Returns a streaming generator of response tokens.
        Also yields a final metadata dict as the last event:
          {"__meta__": True, "confidence": "high", "sources": [...]}
        """
        # ── 1. Determine if we should allow all documents (Permission-based) ─
        allow_all = False
        if document_id:
            # Detect keywords in query that signal permission grant
            q_clean = query.strip().upper()
            if q_clean in ["YES", "OK", "Y", "REFER ALL", "PROCEED", "YES PLEASE", "PLEASE REFER ALL", "REFER ALL DOCUMENTS"]:
                allow_all = True
                print(f"[AIChatService] Cross-document permission granted via query: '{query}'")

        # ── 2. Retrieve Context ──────────────────────────────────────────────
        effective_doc_id = None if allow_all else document_id
        chunks, doc_context = await self._fetch_chunk_context(patient_id, effective_doc_id)
        
        # Only fetch SOAP context if we're not focusing on a specific document (or if permission granted)
        soap_context = ""
        if not document_id or allow_all:
            soap_context = await self._fetch_soap_context(patient_id)

        chunk_count = len(chunks)
        confidence = self._compute_confidence(chunk_count)

        print(
            f"[AIChatService] Context — chunks={chunk_count}, confidence={confidence}, "
            f"soap={'yes' if soap_context else 'no'}, "
            f"history_msgs={len(session_history) if session_history else 0}"
        )

        # ── 3. Determine System Prompt based on Context ──────────────────────
        if document_id and not allow_all:
            system_prompt = DOCUMENT_SPECIFIC_SYSTEM_PROMPT
        else:
            system_prompt = MEDICAL_SYSTEM_PROMPT
            
        if not chunks and not soap_context:
            system_prompt = GENERAL_MEDICAL_PROMPT

        # ── 3. Build Structured Context for Prompt ───────────────────────────
        context_sections = []

        if doc_context:
            context_sections.append(
                "=== PATIENT MEDICAL DOCUMENTS ===\n"
                "The following text was extracted from the patient's uploaded medical records.\n"
                "Use ONLY this content to answer:\n\n"
                + doc_context
            )

        if soap_context:
            context_sections.append(
                "=== PAST CONSULTATION SOAP NOTES ===\n"
                "The following SOAP notes are from the patient's previous consultations:\n\n"
                + soap_context
            )

        context_text = "\n\n".join(context_sections)

        # ── 4. Build Claude Message List with History ─────────────────────────
        messages = []

        # Inject prior session history as conversation context
        if session_history:
            messages.extend(session_history)

        # Add the current question
        messages.append({"role": "user", "content": query})

        # ── 5. Stream from Bedrock with Guardrail Prompt ──────────────────────
        full_response = ""
        bedrock_failed = False

        try:
            async for token in aws_service.generate_chat_stream(
                messages=messages,
                context=context_text,
                system_prompt_override=system_prompt,
            ):
                full_response += token
                yield token

        except Exception as e:
            print(f"[AIChatService] Bedrock streaming failed: {e}")
            bedrock_failed = True

        if bedrock_failed:
            yield FALLBACK_BEDROCK_UNAVAILABLE
            return

        # ── 6. Yield Metadata (so caller can persist sources + confidence) ────
        source_labels = [c.source for c in chunks]

        # Yield structured metadata as a special final event
        import json as _json
        yield (
            f"\n__META__:{_json.dumps({'confidence': confidence, 'sources': source_labels})}"
        )
