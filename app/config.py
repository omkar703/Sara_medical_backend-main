"""Application Configuration"""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    APP_NAME: str = "Saramedico"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_VERSION: str = "1.0.0"
    APP_SECRET_KEY: str
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 4
    API_V1_PREFIX: str = "/api/v1"
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    # Security
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ENCRYPTION_KEY: str  # Fernet key for PII encryption
    
    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_TIMEOUT: int = 30
    
    # Redis
    REDIS_URL: str
    REDIS_DB_CACHE: int = 0
    REDIS_DB_SESSIONS: int = 1
    REDIS_DB_CELERY: int = 2
    
    # MinIO
    MINIO_ENDPOINT: str
    MINIO_EXTERNAL_ENDPOINT: Optional[str] = None
    MINIO_ROOT_USER: str
    MINIO_ROOT_PASSWORD: str
    MINIO_USE_SSL: bool = False
    MINIO_BUCKET_UPLOADS: str = "saramedico-uploads"
    MINIO_BUCKET_DOCUMENTS: str = "saramedico-documents"
    MINIO_BUCKET_AUDIO: str = "saramedico-audio"
    MINIO_BUCKET_AVATARS: str = "saramedico-avatars"
    PRESIGNED_URL_EXPIRY: int = 3600
    
    @property
    def minio_presigned_endpoint(self) -> str:
        return self.MINIO_EXTERNAL_ENDPOINT or self.MINIO_ENDPOINT
    
    # Email
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str
    SMTP_FROM_NAME: str
    SMTP_TLS: bool = False
    SMTP_SSL: bool = False
    
    # Celery
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: str = "json"
    CELERY_TIMEZONE: str = "UTC"
    
    # MFA
    MFA_ENABLED: bool = True
    MFA_ISSUER_NAME: str = "Saramedico"
    TOTP_SECRET_LENGTH: int = 32
    OTP_EXPIRY_SECONDS: int = 300
    OTP_RESEND_COOLDOWN_SECONDS: int = 60
    OTP_MAX_ATTEMPTS: int = 5
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    LOGIN_RATE_LIMIT_PER_MINUTE: int = 5
    
    # File Uploads
    MAX_UPLOAD_SIZE_MB: int = 100
    ALLOWED_FILE_EXTENSIONS: str = "pdf,jpg,jpeg,png,gif,wav,mp3,m4a,webm,dicom,docx,txt"
    
    @property
    def allowed_extensions_list(self) -> List[str]:
        return [ext.strip() for ext in self.ALLOWED_FILE_EXTENSIONS.split(",")]
    
    # Audit Logging
    AUDIT_LOG_ENABLED: bool = True
    AUDIT_LOG_RETENTION_DAYS: int = 2555
    
    # Session Management
    SESSION_EXPIRY_HOURS: int = 24
    MAX_CONCURRENT_SESSIONS: int = 5
    SESSION_IDLE_TIMEOUT_MINUTES: int = 30
    
    # Subscription (Trial Mode)
    TRIAL_DURATION_DAYS: int = 10
    TRIAL_PATIENTS_LIMIT: int = 10
    TRIAL_STORAGE_LIMIT_MB: int = 500
    
    # Logging
    LOG_LEVEL: str = "DEBUG"
    LOG_FORMAT: str = "json"
    LOG_FILE_PATH: str = "logs/saramedico.log"
    
    # Feature Flags
    FEATURE_AI_ANALYSIS: bool = False
    FEATURE_VIDEO_CALLS: bool = False
    FEATURE_SMS_NOTIFICATIONS: bool = False
    FEATURE_REAL_EMAIL: bool = False
    FEATURE_CLOUD_STORAGE: bool = False
    
    # Zoom Configuration
    ZOOM_ACCOUNT_ID: str = ""
    ZOOM_CLIENT_ID: str = ""
    ZOOM_CLIENT_SECRET: str = ""
    ZOOM_ADMIN_EMAIL: str = ""
    ZOOM_BASE_URL: str = "https://api.zoom.us/v2"
    ZOOM_AUTH_URL: str = "https://zoom.us/oauth/token"

    # Social Auth (Google & Apple)
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    APPLE_CLIENT_ID: Optional[str] = None
    APPLE_CLIENT_SECRET: Optional[str] = None  # This must be the generated JWT
    APPLE_REDIRECT_URI: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()