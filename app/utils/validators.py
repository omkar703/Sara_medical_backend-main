"""
File Validation Utilities
"""
import os
from pathlib import Path
from typing import List, Tuple

from fastapi import UploadFile

from app.config import get_settings
from app.models.schemas import FileValidation

settings = get_settings()

# Allowed file extensions
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/jpg"
}


def validate_file_type(filename: str) -> bool:
    """
    Validate file extension
    
    Args:
        filename: Name of the file
        
    Returns:
        True if file type is allowed
    """
    file_ext = Path(filename).suffix.lower()
    return file_ext in ALLOWED_EXTENSIONS


def validate_file_size(file_size: int, max_size: int = None) -> bool:
    """
    Validate file size
    
    Args:
        file_size: Size of file in bytes
        max_size: Maximum allowed size in bytes (default from settings)
        
    Returns:
        True if file size is within limits
    """
    if max_size is None:
        max_size = settings.max_file_size_bytes
    return file_size <= max_size


def validate_batch_size(num_files: int) -> bool:
    """
    Validate number of files in batch
    
    Args:
        num_files: Number of files in batch
        
    Returns:
        True if batch size is within limits
    """
    return num_files <= settings.max_batch_size


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to remove dangerous characters
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove or replace dangerous characters
    dangerous_chars = ['/', '\\', '..', '\x00']
    sanitized = filename
    
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '_')
    
    # Limit filename length
    name, ext = os.path.splitext(sanitized)
    if len(name) > 200:
        name = name[:200]
    
    return f"{name}{ext}"


async def validate_upload_file(file: UploadFile) -> FileValidation:
    """
    Comprehensive file validation
    
    Args:
        file: Uploaded file
        
    Returns:
        FileValidation object with validation results
    """
    # Read file to get size
    content = await file.read()
    file_size = len(content)
    
    # Reset file pointer
    await file.seek(0)
    
    # Validate file type
    if not validate_file_type(file.filename):
        return FileValidation(
            is_valid=False,
            error=f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}",
            file_size=file_size,
            file_type=Path(file.filename).suffix.lower()
        )
    
    # Validate file size
    if not validate_file_size(file_size):
        max_mb = settings.max_file_size_mb
        return FileValidation(
            is_valid=False,
            error=f"File size exceeds maximum allowed size of {max_mb} MB",
            file_size=file_size,
            file_type=Path(file.filename).suffix.lower()
        )
    
    # Validate MIME type (additional check)
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        return FileValidation(
            is_valid=False,
            error=f"Invalid MIME type: {file.content_type}",
            file_size=file_size,
            file_type=Path(file.filename).suffix.lower()
        )
    
    return FileValidation(
        is_valid=True,
        error=None,
        file_size=file_size,
        file_type=Path(file.filename).suffix.lower()
    )


def is_async_processing_required(file_size: int) -> bool:
    """
    Determine if file should be processed asynchronously
    
    Args:
        file_size: File size in bytes
        
    Returns:
        True if async processing is recommended
    """
    return file_size >= settings.async_threshold_bytes


def get_file_extension(filename: str) -> str:
    """
    Get file extension in lowercase
    
    Args:
        filename: Filename
        
    Returns:
        Lowercase file extension without dot
    """
    return Path(filename).suffix.lower().lstrip('.')
