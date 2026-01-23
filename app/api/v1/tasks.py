
from typing import List
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse

router = APIRouter(prefix="/doctor/tasks", tags=["Doctor Tasks"])

async def validate_doctor_role(current_user: User = Depends(get_current_user)):
    if current_user.role != "doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Access restricted to doctors only"
        )
    return current_user

@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_in: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(validate_doctor_role)
):
    """Create a new task for the doctor."""
    task = Task(
        title=task_in.title,
        description=task_in.description,
        due_date=task_in.due_date,
        priority=task_in.priority,
        status=task_in.status,
        doctor_id=current_user.id
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task

@router.get("", response_model=List[TaskResponse])
async def get_tasks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(validate_doctor_role)
):
    """
    Retrieve tasks for the current doctor.
    Sorted by 'urgent' priority first, then by due_date (or creation date).
    """
    # Logic: Urgent first, then others. 
    # For secondary sort, we can use due_date, or created_at desc.
    
    # We can do ordering in SQL.
    # CASE WHEN priority = 'urgent' THEN 0 ELSE 1 END
    
    from sqlalchemy import case
    
    query = select(Task).where(Task.doctor_id == current_user.id)
    
    # Sort: Urgent (0) < Normal (1)
    # Then by due_date ascending (sooner first), nulls last?
    # Or created_at desc? User said "Sort by 'Urgent' first, then by Date."
    
    query = query.order_by(
        case(
            (Task.priority == "urgent", 0),
            else_=1
        ),
        Task.due_date.asc().nulls_last(),
        Task.created_at.desc()
    )
    
    result = await db.execute(query)
    tasks = result.scalars().all()
    return tasks

@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    task_update: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(validate_doctor_role)
):
    """Update a task."""
    result = await db.execute(select(Task).where(Task.id == task_id, Task.doctor_id == current_user.id))
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    update_data = task_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
        
    # Update timestamp
    task.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(task)
    return task

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(validate_doctor_role)
):
    """Delete a task."""
    result = await db.execute(select(Task).where(Task.id == task_id, Task.doctor_id == current_user.id))
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    await db.delete(task)
    await db.commit()
