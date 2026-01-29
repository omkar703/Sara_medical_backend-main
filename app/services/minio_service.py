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
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ROOT_USER,
            secret_key=settings.MINIO_ROOT_PASSWORD,
            secure=settings.MINIO_USE_SSL
        )
        self._ensure_buckets()
    
    def _ensure_buckets(self):
        """Ensure all required buckets exist"""
        buckets = [
            settings.MINIO_BUCKET_UPLOADS,
            settings.MINIO_BUCKET_DOCUMENTS,
            settings.MINIO_BUCKET_AUDIO,
            settings.MINIO_BUCKET_AVATARS,
            "saramedico-medical-records"  # Dedicated bucket for medical history
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
    
    def generate_presigned_url(self, bucket_name: str, object_name: str, expiry_seconds: int = 900) -> Optional[str]:
        """
        Generate a presigned URL for secure, temporary file access.
        Default: 15 minutes (900 seconds) for HIPAA compliance.
        
        Args:
            bucket_name: MinIO bucket name
            object_name: Object path in bucket
            expiry_seconds: URL expiration time (default: 900 = 15 minutes)
        
        Returns:
            Presigned URL string or None if error
        """
        try:
            url = self.client.presigned_get_object(
                bucket_name,
                object_name,
                expires=timedelta(seconds=expiry_seconds)
            )
            return url
        except S3Error as e:
            print(f"Presigned URL generation failed: {e}")
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
            self.client.stat_object(bucket_name, object_name)
            return True
        except S3Error:
            return False


# Global instance
minio_service = MinIOService()
