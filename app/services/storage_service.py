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
        
        # IMPORTANT: presign_client uses the EXTERNAL endpoint (localhost:9010).
        # Presigned URL signatures include the 'host' header, so the client used
        # to sign must match the host the browser will use to fetch the file.
        external_endpoint = settings.minio_presigned_endpoint
        self.presign_client = Minio(
            external_endpoint,
            access_key=settings.MINIO_ROOT_USER,
            secret_key=settings.MINIO_ROOT_PASSWORD,
            secure=settings.MINIO_USE_SSL
        )
        
        self.bucket_name = settings.MINIO_BUCKET_DOCUMENTS
        
        # Pre-populate region map on BOTH clients to avoid network region-discovery pings.
        self.client._region_map[self.bucket_name] = "us-east-1"
        self.presign_client._region_map[self.bucket_name] = "us-east-1"
    
    async def generate_upload_url(
        self, 
        storage_path: str, 
        content_type: str, 
        expires_in: int = 3600
    ) -> str:
        """
        Generate a presigned PUT URL for uploading a file
        """
        if not storage_path or not storage_path.strip():
            raise Exception("Cannot generate upload URL: storage_path is empty")
        from datetime import timedelta
        try:
            # Use presign_client initialized with the external endpoint
            url = self.presign_client.presigned_put_object(
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
    ) -> Optional[str]:
        """
        Generate a presigned GET URL for downloading a file.
        Returns None if storage_path is empty (file not yet uploaded).
        """
        if not storage_path or not storage_path.strip():
            print(f"generate_download_url: skipping, storage_path is empty")
            return None
        from datetime import timedelta
        try:
            # Use presign_client initialized with the external endpoint
            url = self.presign_client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=storage_path.strip(),
                expires=timedelta(seconds=expires_in)
            )
            return url
        except S3Error as e:
            print(f"Failed to generate download URL for '{storage_path}': {e}")
            return None
        except Exception as e:
            print(f"Unexpected error generating download URL for '{storage_path}': {e}")
            return None
    
    async def file_exists(self, storage_path: str) -> bool:
        """
        Check if a file exists in storage.
        Returns False immediately if storage_path is empty.
        """
        clean_path = storage_path.strip() if storage_path else ""
        if not clean_path:
            print(f"file_exists: storage_path is empty, returning False")
            return False
        try:
            print(f"Checking storage: bucket={self.bucket_name}, path='{clean_path}'")
            self.client.stat_object(
                bucket_name=self.bucket_name,
                object_name=clean_path
            )
            return True
        except S3Error as e:
            print(f"Storage check failed for '{clean_path}': {e}")
            return False
        except Exception as e:
            print(f"Unexpected error checking storage for '{clean_path}': {e}")
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
