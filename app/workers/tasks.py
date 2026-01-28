"""Background Tasks"""

from app.workers.celery_app import celery_app


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
    # Simulate scanning
    return f"Document {document_id} scanned: Clean"


@celery_app.task(name="app.workers.tasks.transcribe_consultation_audio")
def transcribe_consultation_audio(consultation_id: str) -> str:
    """
    Placeholder task for audio transcription.
    In production, this would:
    1. Download audio from MinIO
    2. Send to transcription service (Whisper/DG)
    3. Update consultation.transcript
    """
    return f"Consultation {consultation_id} transcription: [Artificial Transcript Placeholder]"


@celery_app.task(name="app.workers.tasks.generate_soap_note")
def generate_soap_note(consultation_id: str) -> str:
    """
    Placeholder task for SOAP note generation.
    In production, this would:
    1. Read consultation transcript
    2. Prompt LLM to generate SOAP note
    3. Update consultation.soap_note
    """
    return f"Consultation {consultation_id} SOAP note generated."


# === AI Processing Tasks ===

import asyncio
from uuid import UUID
from app.database import AsyncSessionLocal
from app.services.document_processor import DocumentProcessor

def run_async(coro):
    """Helper to run async code in a sync Celery task"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    if loop.is_running():
        future = asyncio.run_coroutine_threadsafe(coro, loop)
        return future.result()
    else:
        return loop.run_until_complete(coro)

@celery_app.task(name="app.workers.tasks.process_document")
def process_document_task(document_id_str: str):
    """Celery task to process a document"""
    document_id = UUID(document_id_str)
    
    async def _process():
        async with AsyncSessionLocal() as db:
            processor = DocumentProcessor(db)
            await processor.process_document(document_id)
            
    return run_async(_process())
