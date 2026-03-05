import uuid
import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User

# Import your actual MinIO service and settings
from app.services.minio_service import minio_service
from app.config import settings

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/me/avatar", response_model=dict)
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a profile picture for the currently logged-in user.
    """
    # 1. Validate the file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only images are allowed."
        )
    
    # 2. Generate a secure, unique filename (this will act as the MinIO object name)
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{current_user.id}_{uuid.uuid4().hex}{file_extension}"
    
    # 3. Read the file content
    file_content = await file.read()
    
    # 4. Upload using your custom minio_service (which returns True/False)
    success = minio_service.upload_bytes(
        file_data=file_content,
        bucket_name=settings.MINIO_BUCKET_AVATARS,
        object_name=unique_filename,
        content_type=file.content_type
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload image to MinIO storage."
        )
        
    # 5. Store ONLY the object name in the DB, not the expiring URL
    current_user.avatar_url = unique_filename
    await db.commit()
    await db.refresh(current_user)
    
    # 6. Generate a temporary presigned URL so the frontend can immediately display the new picture
    preview_url = minio_service.generate_presigned_url(
        bucket_name=settings.MINIO_BUCKET_AVATARS,
        object_name=unique_filename
    )
    
    return {
        "message": "Profile picture updated successfully",
        "avatar_object": unique_filename,
        "preview_url": preview_url
    }