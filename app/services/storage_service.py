"""Storage Service for MinIO Integration"""

from typing import Optional
from uuid import UUID

from minio import Minio
from minio.error import S3Error

from app.config import settings


class StorageService:
    """Service for managing file storage with MinIO"""
    
    def __init__(self):
        """Initialize MinIO clients"""
        # Internal client for backend-to-MinIO communication
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ROOT_USER,
            secret_key=settings.MINIO_ROOT_PASSWORD,
            secure=settings.MINIO_USE_SSL
        )
        
        # External client for presigned URLs accessible from outside Docker
        self.external_client = Minio(
            settings.minio_presigned_endpoint,
            access_key=settings.MINIO_ROOT_USER,
            secret_key=settings.MINIO_ROOT_PASSWORD,
            secure=settings.MINIO_USE_SSL
        )
        
        self.bucket_name = settings.MINIO_BUCKET_DOCUMENTS
    
    async def generate_upload_url(
        self, 
        storage_path: str, 
        content_type: str, 
        expires_in: int = 3600
    ) -> str:
        """
        Generate a presigned PUT URL for uploading a file
        
        Args:
            storage_path: Full storage path (e.g., org_id/patient_id/doc_id/filename)
            content_type: MIME type of the file
            expires_in: URL expiration time in seconds (default: 1 hour)
        
        Returns:
            Presigned upload URL
        """
        from datetime import timedelta
        try:
            url = self.external_client.presigned_put_object(
                bucket_name=self.bucket_name,
                object_name=storage_path,
                expires=timedelta(seconds=expires_in)
            )
            return url
        except S3Error as e:
            raise Exception(f"Failed to generate upload URL: {str(e)}")
    
    async def generate_download_url(
        self, 
        storage_path: str, 
        expires_in: int = 3600
    ) -> str:
        """
        Generate a presigned GET URL for downloading a file
        
        Args:
            storage_path: Full storage path
            expires_in: URL expiration time in seconds (default: 1 hour)
        
        Returns:
            Presigned download URL
        """
        from datetime import timedelta
        try:
            url = self.external_client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=storage_path,
                expires=timedelta(seconds=expires_in)
            )
            return url
        except S3Error as e:
            raise Exception(f"Failed to generate download URL: {str(e)}")
    
    async def file_exists(self, storage_path: str) -> bool:
        """
        Check if a file exists in storage
        
        Args:
            storage_path: Full storage path
        
        Returns:
            True if file exists, False otherwise
        """
        try:
            self.client.stat_object(
                bucket_name=self.bucket_name,
                object_name=storage_path
            )
            return True
        except S3Error:
            return False
    
    async def delete_file(self, storage_path: str) -> None:
        """
        Delete a file from storage
        
        Args:
            storage_path: Full storage path
        """
        try:
            self.client.remove_object(
                bucket_name=self.bucket_name,
                object_name=storage_path
            )
        except S3Error as e:
            # Log error but don't raise - allow soft delete to proceed
            print(f"Warning: Failed to delete file from storage: {str(e)}")
    
    @staticmethod
    def generate_storage_path(
        organization_id: UUID,
        patient_id: UUID,
        document_id: UUID,
        filename: str
    ) -> str:
        """
        Generate a structured storage path
        
        Args:
            organization_id: Organization UUID
            patient_id: Patient UUID
            document_id: Document UUID
            filename: Original filename
        
        Returns:
            Storage path in format: org_id/patient_id/doc_id/filename
        """
        return f"{organization_id}/{patient_id}/{document_id}/{filename}"
