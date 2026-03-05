"""Background Tasks"""

import asyncio
import json
from uuid import UUID

from app.workers.celery_app import celery_app


# ─────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────

def run_async(coro):
    """
    Run an async coroutine from a sync Celery task safely.

    With gevent pooling (-P gevent), every Celery task runs inside a greenlet
    that may already have an event loop attached. Using 'get_event_loop()' or
    'run_coroutine_threadsafe()' in that context raises:
        RuntimeError: <loop> is attached to a different loop

    The safe fix: always spin up a *fresh* OS thread that has its own isolated
    asyncio event loop and call asyncio.run() in that thread.
    """
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(asyncio.run, coro)
        return future.result()


# ─────────────────────────────────────────────────────────
# Example / Utility Tasks
# ─────────────────────────────────────────────────────────

@celery_app.task(name="app.workers.tasks.example_task")
def example_task(param: str) -> str:
    """Example Celery task"""
    return f"Task completed with param: {param}"


@celery_app.task(name="app.workers.tasks.scan_document_for_viruses")
def scan_document_for_viruses(document_id: str) -> str:
    """
    Placeholder task for scanning a document for viruses.
    In production, this would download the file from MinIO
    and scan it using ClamAV or similar.
    """
    return f"Document {document_id} scanned: Clean"


# ─────────────────────────────────────────────────────────
# Document Processing Tasks
# ─────────────────────────────────────────────────────────

@celery_app.task(name="app.workers.tasks.process_document")
def process_document_task(document_id_str: str):
    """
    Celery task to process a document.

    Uses SyncDocumentProcessor (psycopg2 + isolated asyncio.run per AWS call)
    to avoid the asyncpg event-loop conflict that gevent causes.
    """
    from app.database import SyncSessionLocal
    from app.services.sync_document_processor import SyncDocumentProcessor

    document_id = UUID(document_id_str)

    db = SyncSessionLocal()
    try:
        processor = SyncDocumentProcessor(db)
        processor.process_document(document_id)
    finally:
        db.close()

# ─────────────────────────────────────────────────────────
# SOAP Note Generation Task
# ─────────────────────────────────────────────────────────

@celery_app.task(
    name="app.workers.tasks.generate_soap_note",
    bind=True,
    max_retries=12,           # e.g., retry up to 12 times (1 hour total)
    default_retry_delay=300,  # 5 minutes
)
def generate_soap_note(self, consultation_id: str) -> dict:
    """
    Background task to generate a SOAP note for a completed consultation.
    Uses Celery retry logic to poll Google Drive until the transcript is ready.
    """
    from app.database import AsyncSessionLocal
    from sqlalchemy import select
    
    # Custom exception to signal that we need to poll again
    class TranscriptNotReady(Exception):
        pass

    async def _run():
        from app.models.consultation import Consultation
        from app.services.google_meet_service import google_meet_service # Real service
        from app.services.aws_service import aws_service

        async with AsyncSessionLocal() as db:
            from sqlalchemy.orm import selectinload
            # 1. Load consultation with eager loading for patient
            result = await db.execute(
                select(Consultation)
                .options(selectinload(Consultation.patient))
                .where(Consultation.id == UUID(consultation_id))
            )
            consultation = result.scalar_one_or_none()

            if not consultation:
                raise ValueError(f"Consultation {consultation_id} not found.")

            if not consultation.google_event_id:
                consultation.ai_status = "failed"
                await db.commit()
                raise ValueError("No google_event_id found for this consultation.")

            # 2. Mark as processing
            consultation.ai_status = "processing"
            await db.commit()

            try:
                # 3. Attempt to fetch the REAL transcript
                transcript_text = await google_meet_service.get_meeting_transcript(
                    consultation.google_event_id
                )

                if not transcript_text:
                    # Not found yet! Raise our custom exception to trigger retry
                    raise TranscriptNotReady("Transcript not yet available in Drive.")

                # 4. Build optional patient context for the prompt
                patient_info = None
                if consultation.patient:
                    patient_info = {
                        "patient_mrn": consultation.patient.mrn,
                        "consultation_id": str(consultation.id),
                        "scheduled_at": consultation.scheduled_at.isoformat(),
                    }

                # 5. Generate SOAP note via AWS Bedrock
                soap_note = await aws_service.generate_soap_note(
                    transcript=transcript_text,
                    patient_info=patient_info,
                )

                # 6. Persist to DB
                consultation.transcript = transcript_text
                consultation.soap_note = soap_note
                consultation.ai_status = "completed"
                await db.commit()

                print(f"[generate_soap_note] ✅ SOAP note generated for consultation {consultation_id}")
                return {
                    "status": "completed",
                    "consultation_id": consultation_id,
                    "soap_note": soap_note,
                }

            except TranscriptNotReady:
                # Re-raise so it escapes the async boundary
                raise
            except Exception as e:
                # Mark as failed on actual errors (Bedrock failure, DB error, etc)
                print(f"[generate_soap_note] ❌ Error for {consultation_id}: {e}")
                consultation.ai_status = "failed"
                await db.commit()
                raise e

    # Execute the async thread and handle the retry logic
    try:
        return run_async(_run())
    except TranscriptNotReady as e:
        print(f"[generate_soap_note] Transcript not ready. Retrying in 5 minutes... (Attempt {self.request.retries + 1}/{self.max_retries})")
        # Trigger Celery retry (countdown is in seconds)
        raise self.retry(exc=e, countdown=300) 
    except Exception as e:
        return {"status": "failed", "reason": str(e)}
