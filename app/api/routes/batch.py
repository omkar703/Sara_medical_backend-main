"""
Batch Upload Endpoint
"""
import uuid
from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException, Query

from app.config import get_settings
from app.models.schemas import BatchUploadResponse, BatchFileInfo, OutputFormat
from app.utils.validators import validate_upload_file, validate_batch_size, sanitize_filename
from app.workers.celery_worker import process_batch_task

settings = get_settings()
router = APIRouter()


@router.post("/ocr/batch", response_model=BatchUploadResponse, tags=["OCR"])
async def batch_upload(
    files: List[UploadFile] = File(..., description="Multiple PDF or image files"),
    output_format: OutputFormat = Query(default=OutputFormat.JSON, description="Output format"),
    extract_entities: bool = Query(default=True, description="Extract medical entities")
):
    """
    Batch upload and process multiple files
    
    - **files**: List of PDF or image files (max 50 files)
    - **output_format**: Return format for all files
    - **extract_entities**: Whether to extract medical entities
    
    Returns batch_id for checking batch status
    """
    # Validate batch size
    if not validate_batch_size(len(files)):
        raise HTTPException(
            status_code=400,
            detail=f"Batch size exceeds maximum of {settings.max_batch_size} files"
        )
    
    # Validate all files
    batch_id = f"batch-{uuid.uuid4()}"
    file_infos = []
    temp_file_paths = []
    filenames = []
    
    settings.create_directories()
    
    for file in files:
        # Validate file
        validation = await validate_upload_file(file)
        if not validation.is_valid:
            # Cleanup already saved files
            for path in temp_file_paths:
                try:
                    path.unlink()
                except:
                    pass
            raise HTTPException(
                status_code=400,
                detail=f"File '{file.filename}' validation failed: {validation.error}"
            )
        
        # Sanitize filename
        safe_filename = sanitize_filename(file.filename)
        filenames.append(safe_filename)
        
        # Save file temporarily
        temp_file_path = settings.upload_dir / f"{batch_id}_{uuid.uuid4()}_{safe_filename}"
        temp_file_paths.append(temp_file_path)
        
        content = await file.read()
        with open(temp_file_path, "wb") as f:
            f.write(content)
        
        # Create file info
        file_infos.append(BatchFileInfo(
            file_name=safe_filename,
            file_size=len(content),
            task_id=f"{batch_id}_{safe_filename}"
        ))
    
    # Enqueue batch processing task
    task = process_batch_task.delay(
        file_paths=[str(p) for p in temp_file_paths],
        filenames=filenames,
        extract_entities=extract_entities,
        output_format=output_format.value
    )
    
    return BatchUploadResponse(
        batch_id=batch_id,
        status="queued",
        files=file_infos,
        total_files=len(files)
    )
