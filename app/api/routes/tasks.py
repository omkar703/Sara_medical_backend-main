"""
Task Status Endpoint
"""
from fastapi import APIRouter, HTTPException
from celery.result import AsyncResult

from app.models.schemas import TaskStatusResponse, TaskStatus, OCRResponse
from app.workers.celery_worker import celery_app

router = APIRouter()


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse, tags=["Tasks"])
async def get_task_status(task_id: str):
    """
    Get status of a background task
    
    - **task_id**: Task identifier returned from OCR extraction or batch upload
    
    Returns task status and results if completed
    """
    # Get task result
    task_result = AsyncResult(task_id, app=celery_app)
    
    if not task_result:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Map Celery state to our TaskStatus
    state = task_result.state
    
    if state == "PENDING":
        status = TaskStatus.PENDING
        progress = 0
        result = None
        error = None
    elif state == "STARTED" or state == "PROGRESS":
        status = TaskStatus.RUNNING
        # Get progress from task meta
        meta = task_result.info or {}
        progress = meta.get("progress", 50)
        result = None
        error = None
    elif state == "SUCCESS":
        status = TaskStatus.COMPLETED
        progress = 100
        # Get result data
        result_data = task_result.result
        if result_data:
            result = OCRResponse(**result_data)
        else:
            result = None
        error = None
    elif state == "FAILURE":
        status = TaskStatus.FAILED
        progress = 0
        result = None
        error = str(task_result.info) if task_result.info else "Task failed"
    else:
        status = TaskStatus.PENDING
        progress = 0
        result = None
        error = None
    
    return TaskStatusResponse(
        task_id=task_id,
        status=status,
        progress=progress,
        result=result,
        error=error
    )
