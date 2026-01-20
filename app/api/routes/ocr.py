"""
OCR Extraction Endpoint
"""
import time
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.models.schemas import OCRResponse, OutputFormat, PageResult, MedicalEntity, EntityType
from app.utils.validators import validate_upload_file, is_async_processing_required, sanitize_filename
from app.services.ocr_service import get_ocr_service
from app.services.medical_extraction import get_medical_extraction_service
from app.services.fhir_mapper import get_fhir_mapper
from app.workers.celery_worker import process_ocr_task

settings = get_settings()
router = APIRouter()


@router.post("/ocr/extract", tags=["OCR"])
async def extract_ocr(
    file: UploadFile = File(..., description="PDF or Image file to process"),
    output_format: OutputFormat = Query(default=OutputFormat.JSON, description="Output format: json or fhir"),
    extract_entities: bool = Query(default=True, description="Extract medical entities")
):
    """
    Extract text and medical entities from uploaded file
    
    - **file**: PDF or image file (PNG, JPG, JPEG)
    - **output_format**: Return format (json or fhir)
    - **extract_entities**: Whether to extract medical entities
    
    For small files (<5MB): Returns results immediately
    For large files (>=5MB): Returns task_id for async processing
    """
    # Validate file
    validation = await validate_upload_file(file)
    if not validation.is_valid:
        raise HTTPException(status_code=400, detail=validation.error)
    
    # Sanitize filename
    safe_filename = sanitize_filename(file.filename)
    
    # Read file content
    file_content = await file.read()
    file_size = len(file_content)
    
    # Check if async processing is needed
    if is_async_processing_required(file_size):
        # Save file temporarily for async processing
        settings.create_directories()
        temp_file_path = settings.upload_dir / f"{uuid.uuid4()}_{safe_filename}"
        
        with open(temp_file_path, "wb") as f:
            f.write(file_content)
        
        # Enqueue background task
        task = process_ocr_task.delay(
            file_path=str(temp_file_path),
            filename=safe_filename,
            extract_entities=extract_entities,
            output_format=output_format.value
        )
        
        return JSONResponse(
            status_code=202,
            content={
                "task_id": task.id,
                "status": "queued",
                "file_name": safe_filename,
                "message": "File is being processed in background. Use /tasks/{task_id} to check status."
            }
        )
    
    # Process synchronously for small files
    try:
        start_time = time.time()
        
        # Get services
        ocr_service = get_ocr_service()
        
        # Process file
        page_results = await ocr_service.process_file(file_content, safe_filename)
        
        # Build page results
        pages = []
        all_text = ""
        total_confidence = 0.0
        
        for page_num, (text, confidence) in enumerate(page_results, 1):
            all_text += text + "\n\n"
            total_confidence += confidence
            
            page_entities = []
            if extract_entities:
                extraction_service = get_medical_extraction_service()
                entities = extraction_service.extract_all_entities(text)
                page_entities = entities
            
            pages.append(PageResult(
                page_number=page_num,
                text=text,
                confidence=confidence,
                entities=page_entities
            ))
        
        avg_confidence = total_confidence / len(page_results) if page_results else 0.0
        
        # Extract all entities from full text
        all_entities = []
        if extract_entities:
            extraction_service = get_medical_extraction_service()
            all_entities = extraction_service.extract_all_entities(all_text)
        
        # Generate FHIR if requested
        fhir_bundle = None
        if output_format == OutputFormat.FHIR and all_entities:
            fhir_mapper = get_fhir_mapper()
            fhir_bundle = fhir_mapper.generate_fhir_bundle(all_text, all_entities)
        
        processing_time = (time.time() - start_time) * 1000
        
        return OCRResponse(
            status="completed",
            file_name=safe_filename,
            pages=pages,
            entities=all_entities,
            overall_confidence=round(avg_confidence, 2),
            processing_time_ms=round(processing_time, 2),
            output_format=output_format,
            fhir_bundle=fhir_bundle
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")
