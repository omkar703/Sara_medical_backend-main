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
    Run an async coroutine from a sync Celery task safely, especially under gevent.
    Spins up a fresh OS thread with its own isolated asyncio event loop.
    """
    import concurrent.futures
    import asyncio

    def _threaded_run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(_threaded_run)
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
    max_retries=3,
    default_retry_delay=30,
)
def generate_soap_note(self, consultation_id: str) -> dict:
    """
    Background task to generate a SOAP note for a completed consultation.

    IMPORTANT: This task requires a REAL Google Meet transcript to generate a SOAP note.
    It will NEVER fall back to mock/demo data as that would produce fabricated clinical records.

    Flow:
    1. Verify the consultation has a google_event_id (i.e., a real meeting was scheduled).
    2. Attempt to fetch the real transcript from Google Drive (attached to the Calendar event).
    3. If transcript is not ready yet, retry up to 3 times (90s total).
    4. If no transcript is available after retries → set ai_status = "no_transcript" and STOP.
    5. If real transcript found → send to AWS Bedrock and save SOAP note.
    """
    from app.database import SyncSessionLocal
    from app.models.consultation import Consultation
    from app.services.google_meet_service import google_meet_service
    from app.services.aws_service import aws_service

    db = SyncSessionLocal()
    try:
        # 1. Fetch consultation
        consultation = db.query(Consultation).filter(Consultation.id == UUID(consultation_id)).first()
        if not consultation:
            return {"status": "failed", "reason": f"Consultation {consultation_id} not found"}

        # 2. Safety check: No real meeting = no transcript = no SOAP note
        if not consultation.google_event_id:
            print(f"[generate_soap_note] ⚠ Consultation {consultation_id} has no google_event_id. "
                  "Cannot generate SOAP note without a real meeting transcript.")
            consultation.ai_status = "no_transcript"
            db.commit()
            return {"status": "no_transcript", "reason": "No Google Meet event associated with this consultation"}

        # 3. Mark as processing
        consultation.ai_status = "processing"
        db.commit()

        # 4. Attempt to fetch REAL transcript from Google Drive
        transcript_text = None
        try:
            transcript_text = run_async(google_meet_service.get_meeting_transcript(consultation.google_event_id))
        except Exception as e:
            print(f"[generate_soap_note] Error fetching transcript: {e}")

        # 5. Handle missing transcript — retry a few times or fail gracefully
        if not transcript_text or not transcript_text.strip():
            print(f"[generate_soap_note] No transcript found yet for Event ID: {consultation.google_event_id}.")

            if self.request.retries < self.max_retries:
                retry_attempt = self.request.retries + 1
                print(f"[generate_soap_note] Retrying in 30s (Attempt {retry_attempt}/{self.max_retries})...")
                raise self.retry(countdown=30)

            # All retries exhausted — meeting had no transcript (e.g., no speech, or transcription disabled)
            print(f"[generate_soap_note] ⚠ No real transcript available after all retries. "
                  "Marking as 'no_transcript'. No SOAP note will be generated.")
            consultation.ai_status = "no_transcript"
            db.commit()
            return {
                "status": "no_transcript",
                "reason": (
                    "No transcript was captured for this meeting. "
                    "Ensure Google Meet transcription is enabled and that the meeting "
                    "contained actual spoken conversation."
                )
            }

        # 6. Real transcript found — build patient context
        print(f"[generate_soap_note] ✅ Real transcript found! Sending to AWS Bedrock...")
        patient_info = None
        if consultation.patient_id:
            patient_info = {
                "consultation_id": str(consultation.id),
                "scheduled_at": consultation.scheduled_at.isoformat() if consultation.scheduled_at else None,
            }

        # 7. Generate SOAP note via AWS Bedrock (Claude 3.5 Sonnet)
        try:
            soap_note = run_async(aws_service.generate_soap_note(
                transcript=transcript_text,
                patient_info=patient_info
            ))

            # 8. Persist results
            consultation.transcript = transcript_text
            consultation.soap_note = soap_note
            consultation.ai_status = "completed"
            db.commit()

            print(f"[generate_soap_note] ✅ SOAP note generated for consultation {consultation_id}")
            return {"status": "completed", "consultation_id": consultation_id}

        except Exception as e:
            print(f"[generate_soap_note] ❌ Bedrock Error: {e}")
            consultation.ai_status = "failed"
            db.commit()
            return {"status": "failed", "reason": str(e)}

    finally:
        db.close()

