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
            secure=False
        )

        # Handle MINIO_EXTERNAL_ENDPOINT which may contain a path (e.g. saramedico.com/s3).
        # MinIO SDK does NOT accept paths in the endpoint — only host[:port].
        # If a path-based endpoint is configured, we sign with the internal client
        # and rewrite the resulting URL to the external path manually.
        external = settings.MINIO_EXTERNAL_ENDPOINT or ""

        if external and "/" in external.lstrip("https://").lstrip("http://"):
            # Path-based endpoint: sign internally, rewrite URL later
            self._external_url_prefix = external.rstrip("/")
            self.presign_client = self.client
            self._rewrite_presigned_urls = True
        elif external:
            # Plain host/port endpoint
            clean_external = external.replace("https://", "").replace("http://", "").rstrip("/")
            self.presign_client = Minio(
                clean_external,
                access_key=settings.MINIO_ROOT_USER,
                secret_key=settings.MINIO_ROOT_PASSWORD,
                secure=settings.MINIO_USE_SSL
            )
            self._external_url_prefix = None
            self._rewrite_presigned_urls = False
        else:
            self.presign_client = self.client
            self._external_url_prefix = None
            self._rewrite_presigned_urls = False

        self.bucket_name = settings.MINIO_BUCKET_DOCUMENTS

        # Pre-populate region map to avoid network region-discovery pings.
        self.client._region_map[self.bucket_name] = "us-east-1"
        if self.presign_client is not self.client:
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
            url = self.presign_client.presigned_put_object(
                bucket_name=self.bucket_name,
                object_name=storage_path,
                expires=timedelta(seconds=expires_in)
            )
            if self._rewrite_presigned_urls and self._external_url_prefix:
                from urllib.parse import urlparse, urlunparse
                parsed = urlparse(url)
                # Replace scheme+host with external prefix
                ext = self._external_url_prefix
                if "://" in ext:
                    new_scheme, new_rest = ext.split("://", 1)
                else:
                    new_scheme = "https"
                    new_rest = ext
                new_host, _, new_base_path = new_rest.partition("/")
                new_path = f"/{new_base_path}/{parsed.path.lstrip('/')}" if new_base_path else parsed.path
                url = urlunparse((new_scheme, new_host, new_path, parsed.params, parsed.query, parsed.fragment))
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
            url = self.presign_client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=storage_path.strip(),
                expires=timedelta(seconds=expires_in)
            )
            if self._rewrite_presigned_urls and self._external_url_prefix:
                from urllib.parse import urlparse, urlunparse
                parsed = urlparse(url)
                ext = self._external_url_prefix
                if "://" in ext:
                    new_scheme, new_rest = ext.split("://", 1)
                else:
                    new_scheme = "https"
                    new_rest = ext
                new_host, _, new_base_path = new_rest.partition("/")
                new_path = f"/{new_base_path}/{parsed.path.lstrip('/')}" if new_base_path else parsed.path
                url = urlunparse((new_scheme, new_host, new_path, parsed.params, parsed.query, parsed.fragment))
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
