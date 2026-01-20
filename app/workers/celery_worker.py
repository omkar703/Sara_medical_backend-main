"""
Celery Worker Configuration and Tasks
"""
import asyncio
import time
from pathlib import Path
from typing import Dict, List

from celery import Celery
from celery.signals import task_prerun, task_postrun

from app.config import get_settings
from app.services.ocr_service import get_ocr_service
from app.services.medical_extraction import get_medical_extraction_service
from app.services.fhir_mapper import get_fhir_mapper
from app.models.schemas import OutputFormat, PageResult, MedicalEntity

settings = get_settings()

# Initialize Celery app
celery_app = Celery(
    "healthcare_ocr",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend
)

# Celery configuration
celery_app.conf.update(
    task_track_started=settings.celery_task_track_started,
    task_time_limit=settings.celery_task_time_limit,
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    task_routes={
        'app.workers.celery_worker.process_ocr_task': {'queue': 'ocr'},
        'app.workers.celery_worker.process_batch_task': {'queue': 'batch'},
    }
)


@task_prerun.connect
def task_prerun_handler(task_id, task, *args, **kwargs):
    """Handler before task execution"""
    print(f"Task {task.name}[{task_id}] starting...")


@task_postrun.connect
def task_postrun_handler(task_id, task, *args, **kwargs):
    """Handler after task execution"""
    print(f"Task {task.name}[{task_id}] completed")


@celery_app.task(name="process_ocr_task", bind=True, max_retries=3)
def process_ocr_task(
    self,
    file_path: str,
    filename: str,
    extract_entities: bool = True,
    output_format: str = "json"
) -> Dict:
    """
    Background task for OCR processing
    
    Args:
        self: Celery task instance
        file_path: Path to uploaded file
        filename: Original filename
        extract_entities: Whether to extract medical entities
        output_format: Output format ('json' or 'fhir')
        
    Returns:
        Processing results dictionary
    """
    try:
        start_time = time.time()
        
        # Update task state
        self.update_state(
            state='PROGRESS',
            meta={'status': 'Reading file...', 'progress': 10}
        )
        
        # Read file
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        # Get services
        ocr_service = get_ocr_service()
        
        # Process file with OCR
        self.update_state(
            state='PROGRESS',
            meta={'status': 'Running OCR...', 'progress': 30}
        )
        
        # Run OCR in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        page_results = loop.run_until_complete(
            ocr_service.process_file(file_data, filename)
        )
        loop.close()
        
        # Build page results
        pages = []
        all_text = ""
        total_confidence = 0.0
        
        for page_num, (text, confidence) in enumerate(page_results, 1):
            all_text += text + "\n\n"
            total_confidence += confidence
            
            page_data = {
                "page_number": page_num,
                "text": text,
                "confidence": confidence,
                "entities": []
            }
            pages.append(page_data)
        
        avg_confidence = total_confidence / len(page_results) if page_results else 0.0
        
        # Extract medical entities if requested
        all_entities = []
        if extract_entities:
            self.update_state(
                state='PROGRESS',
                meta={'status': 'Extracting medical entities...', 'progress': 60}
            )
            
            extraction_service = get_medical_extraction_service()
            entities = extraction_service.extract_all_entities(all_text)
            
            # Convert to dict format
            all_entities = [
                {
                    "entity_type": e.entity_type.value,
                    "value": e.value,
                    "confidence": e.confidence,
                    "normalized_value": e.normalized_value,
                    "unit": e.unit
                }
                for e in entities
            ]
        
        # Generate FHIR output if requested
        fhir_bundle = None
        if output_format == "fhir" and all_entities:
            self.update_state(
                state='PROGRESS',
                meta={'status': 'Generating FHIR resources...', 'progress': 80}
            )
            
            fhir_mapper = get_fhir_mapper()
            # Reconstruct entities from dict
            from app.models.schemas import MedicalEntity, EntityType
            entity_objects = [
                MedicalEntity(
                    entity_type=EntityType(e["entity_type"]),
                    value=e["value"],
                    confidence=e["confidence"],
                    normalized_value=e["normalized_value"],
                    unit=e["unit"]
                )
                for e in all_entities
            ]
            fhir_bundle = fhir_mapper.generate_fhir_bundle(all_text, entity_objects)
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Cleanup uploaded file
        try:
            Path(file_path).unlink()
        except Exception:
            pass
        
        # Return results
        result = {
            "status": "completed",
            "file_name": filename,
            "pages": pages,
            "entities": all_entities,
            "overall_confidence": round(avg_confidence, 2),
            "processing_time_ms": round(processing_time, 2),
            "output_format": output_format,
            "fhir_bundle": fhir_bundle
        }
        
        return result
        
    except Exception as exc:
        # Retry on failure
        raise self.retry(exc=exc, countdown=5)


@celery_app.task(name="process_batch_task", bind=True)
def process_batch_task(
    self,
    file_paths: List[str],
    filenames: List[str],
    extract_entities: bool = True,
    output_format: str = "json"
) -> Dict:
    """
    Background task for batch processing
    
    Args:
        self: Celery task instance
        file_paths: List of file paths
        filenames: List of original filenames
        extract_entities: Whether to extract entities
        output_format: Output format
        
    Returns:
        Batch processing results
    """
    results = []
    total_files = len(file_paths)
    
    for idx, (file_path, filename) in enumerate(zip(file_paths, filenames), 1):
        # Update progress
        progress = int((idx / total_files) * 100)
        self.update_state(
            state='PROGRESS',
            meta={
                'status': f'Processing file {idx}/{total_files}',
                'progress': progress,
                'completed': idx - 1,
                'total': total_files
            }
        )
        
        # Process individual file
        try:
            result = process_ocr_task(
                file_path=file_path,
                filename=filename,
                extract_entities=extract_entities,
                output_format=output_format
            )
            results.append(result)
        except Exception as e:
            results.append({
                "status": "failed",
                "file_name": filename,
                "error": str(e)
            })
    
    return {
        "status": "completed",
        "total_files": total_files,
        "successful": sum(1 for r in results if r.get("status") == "completed"),
        "failed": sum(1 for r in results if r.get("status") == "failed"),
        "results": results
    }


@celery_app.task(name="cleanup_old_files")
def cleanup_old_files():
    """Periodic task to cleanup old temporary files"""
    import time
    from datetime import datetime, timedelta
    
    # Cleanup files older than 24 hours
    cutoff_time = time.time() - (24 * 60 * 60)
    
    for directory in [settings.upload_dir, settings.temp_dir, settings.result_dir]:
        if not directory.exists():
            continue
        
        for file_path in directory.glob("*"):
            if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                try:
                    file_path.unlink()
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")
