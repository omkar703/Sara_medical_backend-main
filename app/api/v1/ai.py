"""AI Integration API - Persistent chat sessions + Document processing"""

import json as _json
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Literal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.ai_processing_queue import AIProcessingQueue
from app.services.permission_service import PermissionService
from app.services.ai_chat_service import AIChatService
from app.services.chat_session_service import ChatSessionService

router = APIRouter(prefix="/doctor/ai", tags=["AI Integration"])


# ══════════════════════════════════════════════════════════════════════════════
# Schemas
# ══════════════════════════════════════════════════════════════════════════════

class DocumentProcessRequest(BaseModel):
    patient_id: UUID
    document_id: UUID = Field(..., description="ID of the document to process")
    processing_type: Literal["comprehensive", "vision_only", "text_only"] = "comprehensive"
    priority: Literal["normal", "high"] = "normal"

    class Config:
        frozen = True


class DocumentProcessResponse(BaseModel):
    job_id: UUID
    status: str
    message: str


class CreateSessionRequest(BaseModel):
    patient_id: UUID
    title: Optional[str] = Field(None, max_length=255, description="Custom session name. Auto-generated if omitted.")


class SessionResponse(BaseModel):
    session_id: UUID
    title: Optional[str]
    patient_id: UUID
    created_at: str
    updated_at: str


class SessionSummaryResponse(BaseModel):
    session_id: UUID
    title: Optional[str]
    updated_at: str


class MessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    sources: Optional[List[str]]
    confidence: Optional[str]
    created_at: str


class SessionDetailResponse(BaseModel):
    session_id: UUID
    title: Optional[str]
    patient_id: UUID
    messages: List[MessageResponse]


class SendMessageRequest(BaseModel):
    session_id: UUID
    patient_id: UUID
    message: str = Field(..., min_length=2, max_length=4000)
    document_id: Optional[UUID] = None


# ══════════════════════════════════════════════════════════════════════════════
# Document Processing (existing, unchanged)
# ══════════════════════════════════════════════════════════════════════════════

@router.post("/process-document", response_model=DocumentProcessResponse, status_code=status.HTTP_201_CREATED)
async def process_document(
    request: DocumentProcessRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Queue a document for AI processing (Textract + Bedrock)."""
    if current_user.role not in ["doctor", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Doctor or Admin role required")

    permission_service = PermissionService(db)
    has_permission = await permission_service.check_doctor_access(
        doctor_id=current_user.id,
        patient_id=request.patient_id
    )
    if not has_permission:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access to patient data not granted.")

    queue_entry = AIProcessingQueue(
        patient_id=request.patient_id,
        doctor_id=current_user.id,
        organization_id=current_user.organization_id,
        data_payload={"document_id": str(request.document_id), "processing_type": request.processing_type},
        request_type=request.processing_type,
        status="pending"
    )
    db.add(queue_entry)
    await db.commit()
    await db.refresh(queue_entry)

    from app.workers.mock_tasks import process_document_task
    process_document_task.delay(str(request.document_id))

    queue_entry.status = "completed"
    await db.commit()

    return DocumentProcessResponse(
        job_id=queue_entry.id,
        status="completed",
        message=f"Document queued for AI processing. Job ID: {queue_entry.id}"
    )


@router.get("/process-document/{job_id}", response_model=DocumentProcessResponse)
async def get_document_processing_status(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Check the status of a document processing job."""
    if current_user.role not in ["doctor", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    result = await db.execute(select(AIProcessingQueue).where(AIProcessingQueue.id == job_id))
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    return DocumentProcessResponse(
        job_id=job.id,
        status=job.status,
        message=job.error_message or f"Job is currently {job.status}"
    )


# ══════════════════════════════════════════════════════════════════════════════
# Chat Sessions (new persistent session management)
# ══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/chat/session",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new AI chat session for a patient",
)
async def create_chat_session(
    request: CreateSessionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new persistent AI chat session scoped to a doctor–patient pair.

    The doctor must have:
    1. `data_access_grant` (general record access)
    2. `ai_access_permission = True` on that grant

    An optional `title` can be provided; if omitted it will be auto-generated
    from the first message sent to the session.
    """
    if current_user.role != "doctor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only doctors can start AI chat sessions")

    perm = PermissionService(db)

    if not await perm.check_doctor_access(current_user.id, request.patient_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access granted for this patient")

    if not await perm.check_ai_access(current_user.id, request.patient_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Doctor does not have AI access permission for this patient."
        )

    session_svc = ChatSessionService(db)
    session = await session_svc.create_session(
        doctor_id=current_user.id,
        patient_id=request.patient_id,
        title=request.title,
    )

    return SessionResponse(
        session_id=session.id,
        title=session.title,
        patient_id=session.patient_id,
        created_at=session.created_at.isoformat(),
        updated_at=session.updated_at.isoformat(),
    )


@router.get(
    "/chat/sessions",
    response_model=List[SessionSummaryResponse],
    summary="List all AI chat sessions for a patient (sidebar)",
)
async def list_chat_sessions(
    patient_id: UUID = Query(..., description="Patient UUID to fetch sessions for"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return a list of this doctor's AI chat sessions for a specific patient,
    ordered by most recently active. Used to populate the ChatGPT-style sidebar.
    """
    if current_user.role != "doctor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only doctors can access chat sessions")

    perm = PermissionService(db)
    if not await perm.check_doctor_access(current_user.id, patient_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access to this patient")

    session_svc = ChatSessionService(db)
    sessions = await session_svc.list_sessions(doctor_id=current_user.id, patient_id=patient_id)

    return [
        SessionSummaryResponse(
            session_id=s.id,
            title=s.title or "Untitled Chat",
            updated_at=s.updated_at.isoformat(),
        )
        for s in sessions
    ]


@router.get(
    "/chat/session/{session_id}",
    response_model=SessionDetailResponse,
    summary="Get a session with its full message history",
)
async def get_chat_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Fetch a chat session and its last 50 messages in chronological order.
    Only the owning doctor can access this session.
    """
    if current_user.role != "doctor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only doctors can access chat sessions")

    session_svc = ChatSessionService(db)
    session = await session_svc.get_session(session_id=session_id, doctor_id=current_user.id)

    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found or access denied")

    messages = await session_svc.get_session_messages(session_id=session_id, limit=50)

    return SessionDetailResponse(
        session_id=session.id,
        title=session.title or "Untitled Chat",
        patient_id=session.patient_id,
        messages=[
            MessageResponse(
                id=m.id,
                role=m.role,
                content=m.content,
                sources=m.sources,
                confidence=m.confidence,
                created_at=m.created_at.isoformat(),
            )
            for m in messages
        ],
    )


@router.post(
    "/chat/message",
    summary="Send a message to an AI chat session (streaming SSE)",
)
async def send_chat_message(
    request: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Send a doctor's message to an existing session and receive a streaming AI response.

    **Response**: `text/event-stream` — tokens are streamed as they are generated by Claude.

    **Flow**:
    1. Validate AI access permission
    2. Load session + last 10 messages (conversation memory)
    3. Run RAG (doc chunks + SOAP notes)
    4. Apply medical guardrails & confidence scoring
    5. Stream Claude response
    6. Persist both messages to `chat_messages` table
    7. Auto-generate session title on first message if none set
    """
    if current_user.role != "doctor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only doctors can chat with AI")

    perm = PermissionService(db)

    if not await perm.check_doctor_access(current_user.id, request.patient_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access to this patient")

    if not await perm.check_ai_access(current_user.id, request.patient_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Doctor does not have AI access permission for this patient."
        )

    session_svc = ChatSessionService(db)
    session = await session_svc.get_session(session_id=request.session_id, doctor_id=current_user.id)

    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found or access denied")

    # Load conversation history for context
    session_history = await session_svc.get_session_history_for_prompt(
        session_id=request.session_id
    )

    ai_service = AIChatService(db)

    async def _stream_and_persist():
        """Inner generator: streams tokens and persists after completion."""
        full_response = ""
        confidence = "low"
        sources: List[str] = []

        async for token in ai_service.chat_with_patient_data(
            patient_id=request.patient_id,
            query=request.message,
            requesting_user=current_user,
            document_id=request.document_id,
            session_history=session_history,
        ):
            # Detect internal metadata event (not streamed to frontend)
            if token.startswith("\n__META__:"):
                try:
                    meta = _json.loads(token.replace("\n__META__:", ""))
                    confidence = meta.get("confidence", "low")
                    sources = meta.get("sources", [])
                except Exception:
                    pass
                continue  # Don't yield metadata token to client

            full_response += token
            yield token

        # Persist both messages
        await session_svc.save_messages(
            session_id=request.session_id,
            doctor_message=request.message,
            ai_response=full_response,
            sources=sources,
            confidence=confidence,
        )

        # Auto-generate title on first message
        if session.title is None and full_response:
            title = await session_svc.auto_generate_title(request.message)
            await session_svc.set_title(request.session_id, title)

    return StreamingResponse(_stream_and_persist(), media_type="text/event-stream")


# ══════════════════════════════════════════════════════════════════════════════
# Legacy Chat (kept for backward compatibility, but deprecated)
# ══════════════════════════════════════════════════════════════════════════════

class DoctorChatRequest(BaseModel):
    patient_id: Optional[UUID] = None
    document_id: Optional[UUID] = None
    query: str = Field(..., min_length=2, max_length=2000)
    conversation_id: Optional[str] = None


@router.post("/chat/doctor", deprecated=True, include_in_schema=True, summary="[Deprecated] Stateless doctor chat")
async def chat_doctor_legacy(
    request: DoctorChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    **Deprecated** — Use `POST /ai/chat/session` + `POST /ai/chat/message` instead.
    Kept for backward compatibility only.
    """
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can use this endpoint")

    if request.patient_id:
        perm_service = PermissionService(db)
        if not await perm_service.check_doctor_access(current_user.id, request.patient_id):
            raise HTTPException(status_code=403, detail="No access to this patient's data")
        if not await perm_service.check_ai_access(current_user.id, request.patient_id):
            raise HTTPException(status_code=403, detail="No AI access to this patient's data")

    service = AIChatService(db)

    async def _legacy_stream():
        async for token in service.chat_with_patient_data(
            patient_id=request.patient_id,
            query=request.query,
            requesting_user=current_user,
            document_id=request.document_id,
        ):
            if not token.startswith("\n__META__:"):
                yield token

    return StreamingResponse(_legacy_stream(), media_type="text/event-stream")


@router.get("/chat-history/doctor", summary="[Deprecated] Get legacy chat history")
async def get_doctor_history(
    patient_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    **Deprecated** — Use `GET /ai/chat/sessions` + `GET /ai/chat/session/{id}` instead.
    """
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Access denied")

    doctor_id = current_user.id
    if patient_id:
        perm_service = PermissionService(db)
        if not await perm_service.check_doctor_access(doctor_id, patient_id):
            raise HTTPException(status_code=403, detail="No access")

    from app.models.chat_history import ChatHistory
    stmt = select(ChatHistory).where(ChatHistory.doctor_id == doctor_id)
    if patient_id:
        stmt = stmt.where(ChatHistory.patient_id == patient_id)
    else:
        stmt = stmt.where(ChatHistory.patient_id.is_(None))
    stmt = stmt.order_by(ChatHistory.created_at.desc())
    result = await db.execute(stmt)
    history = result.scalars().all()
    return {"history": history}
