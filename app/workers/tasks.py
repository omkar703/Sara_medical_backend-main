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
