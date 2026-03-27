"""MinIO Service - S3-compatible object storage with presigned URLs"""

from datetime import timedelta
from typing import Optional
from minio import Minio
from minio.error import S3Error

from app.config import settings


class MinIOService:
    """
    MinIO service for secure file storage with presigned URLs.
    HIPAA Compliance: All URLs are temporary (default 15 minutes).
    """
    
    def __init__(self):
        # Internal client for backend-to-MinIO communication (bucket checks, uploads, etc.)
        # Internal Docker network does not use SSL, so secure=False always.
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ROOT_USER,
            secret_key=settings.MINIO_ROOT_PASSWORD,
            secure=False
        )
        
        # IMPORTANT: presign_client uses the EXTERNAL endpoint (localhost:9010).
        # Presigned URL signatures include the 'host' header, so the client used
        # to sign must match the host the browser will use to fetch the file.
        # If we sign with 'minio:9000' but serve 'localhost:9010', MinIO returns
        # SignatureDoesNotMatch.
        external_endpoint = settings.minio_presigned_endpoint
        self.presign_client = Minio(
            external_endpoint,
            access_key=settings.MINIO_ROOT_USER,
            secret_key=settings.MINIO_ROOT_PASSWORD,
            secure=settings.MINIO_USE_SSL
        )
        
        # Bucket management MUST use internal client (self.client) 
        # because the backend container can't reach 'localhost:9010' from inside Docker.
        self._ensure_buckets()

        # Pre-populate region map on BOTH clients to avoid network region-discovery pings.
        # Without this, the library tries to connect to the server to find the region,
        # which crashes when presign_client tries to connect to localhost:9010 from inside Docker.
        for bucket in [settings.MINIO_BUCKET_UPLOADS, settings.MINIO_BUCKET_DOCUMENTS,
                       settings.MINIO_BUCKET_AUDIO, settings.MINIO_BUCKET_AVATARS]:
            self.client._region_map[bucket] = "us-east-1"
            self.presign_client._region_map[bucket] = "us-east-1"
    
    def _ensure_buckets(self):
        """Ensure all required buckets exist"""
        buckets = [
            settings.MINIO_BUCKET_UPLOADS,
            settings.MINIO_BUCKET_DOCUMENTS,
            settings.MINIO_BUCKET_AUDIO,
            settings.MINIO_BUCKET_AVATARS,
        ]
        
        for bucket in buckets:
            try:
                if not self.client.bucket_exists(bucket):
                    self.client.make_bucket(bucket)
                    print(f"Created bucket: {bucket}")
            except S3Error as e:
                print(f"Bucket {bucket} check failed: {e}")
    
    def upload_file(self, file_path: str, bucket_name: str, object_name: str, content_type: str = "application/octet-stream"):
        """Upload a file to MinIO"""
        try:
            self.client.fput_object(
                bucket_name,
                object_name,
                file_path,
                content_type=content_type
            )
            return True
        except S3Error as e:
            print(f"Upload failed: {e}")
            return False
    
    def upload_bytes(self, file_data: bytes, bucket_name: str, object_name: str, content_type: str = "application/octet-stream"):
        """Upload bytes data to MinIO"""
        from io import BytesIO
        try:
            self.client.put_object(
                bucket_name,
                object_name,
                BytesIO(file_data),
                length=len(file_data),
                content_type=content_type
            )
            return True
        except S3Error as e:
            print(f"Upload failed: {e}")
            return False
    
    def generate_presigned_url(
        self, 
        bucket_name: str, 
        object_name: str, 
        expiry_seconds: int = 900,
        response_headers: Optional[dict] = None
    ) -> Optional[str]:
        """
        Generate a presigned URL for secure, temporary file access.
        Default: 15 minutes (900 seconds) for HIPAA compliance.
        Returns None if object_name is empty.
        """
        if not object_name or not object_name.strip():
            print(f"generate_presigned_url: skipping, object_name is empty")
            return None
        try:
            # Use presign_client (configured with the external endpoint) to generate the URL.
            url = self.presign_client.presigned_get_object(
                bucket_name,
                object_name.strip(),
                expires=timedelta(seconds=expiry_seconds),
                response_headers=response_headers
            )
            return url
        except S3Error as e:
            print(f"Failed to generate presigned URL: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error generating presigned URL: {e}")
            return None
    
    def get_file_bytes(self, bucket_name: str, object_name: str) -> Optional[bytes]:
        """Retrieve file content as bytes."""
        try:
            response = self.client.get_object(bucket_name, object_name)
            return response.read()
        except S3Error as e:
            print(f"Download failed: {e}")
            return None
        finally:
            if 'response' in locals():
                response.close()
                
                
    def delete_file(self, bucket_name: str, object_name: str) -> bool:
        """Delete a file from MinIO"""
        try:
            self.client.remove_object(bucket_name, object_name)
            return True
        except S3Error as e:
            print(f"Delete failed: {e}")
            return False
    
    def file_exists(self, bucket_name: str, object_name: str) -> bool:
        """Check if a file exists in MinIO"""
        try:
            print(f"Minio existence check: bucket={bucket_name}, path='{object_name}'")
            self.client.stat_object(bucket_name, object_name)
            return True
        except S3Error as e:
            print(f"Minio existence check FAILED for '{object_name}' in {bucket_name}: {e}")
            return False
        except Exception as e:
            print(f"Minio existence check ERROR for '{object_name}': {e}")
            return False

    def get_storage_stats(self):
        """Calculate used space and count objects across all buckets"""
        total_size = 0
        total_count = 0
        buckets = [
            settings.MINIO_BUCKET_UPLOADS,
            settings.MINIO_BUCKET_DOCUMENTS,
            settings.MINIO_BUCKET_AUDIO,
            settings.MINIO_BUCKET_AVATARS,
        ]
        
        for bucket in buckets:
            try:
                if self.client.bucket_exists(bucket):
                    objects = self.client.list_objects(bucket, recursive=True)
                    for obj in objects:
                        total_size += obj.size
                        total_count += 1
            except Exception as e:
                print(f"Error getting stats for bucket {bucket}: {e}")
                
        return {
            "used_bytes": total_size,
            "files_count": total_count
        }


# Global instance
minio_service = MinIOService()
