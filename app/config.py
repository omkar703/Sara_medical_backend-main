"""
Configuration Management for Healthcare OCR Backend
"""
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application Settings
    app_name: str = Field(default="Medical OCR Extraction API", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=False, alias="DEBUG")
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    workers: int = Field(default=4, alias="WORKERS")
    
    # Redis Configuration
    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_db: int = Field(default=0, alias="REDIS_DB")
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    
    # Celery Configuration
    celery_broker_url: str = Field(default="redis://localhost:6379/0", alias="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/0", alias="CELERY_RESULT_BACKEND")
    celery_task_track_started: bool = Field(default=True, alias="CELERY_TASK_TRACK_STARTED")
    celery_task_time_limit: int = Field(default=600, alias="CELERY_TASK_TIME_LIMIT")
    
    # File Upload Configuration
    upload_dir: Path = Field(default=Path("/app/uploads"), alias="UPLOAD_DIR")
    result_dir: Path = Field(default=Path("/app/results"), alias="RESULT_DIR")
    temp_dir: Path = Field(default=Path("/app/temp"), alias="TEMP_DIR")
    max_file_size_mb: int = Field(default=50, alias="MAX_FILE_SIZE_MB")
    max_batch_size: int = Field(default=50, alias="MAX_BATCH_SIZE")
    
    # OCR Configuration
    tesseract_cmd: str = Field(default="/usr/bin/tesseract", alias="TESSERACT_CMD")
    tesseract_lang: str = Field(default="eng", alias="TESSERACT_LANG")
    ocr_config: str = Field(default="--oem 3 --psm 6", alias="OCR_CONFIG")
    async_threshold_mb: int = Field(default=5, alias="ASYNC_THRESHOLD_MB")
    
    # FHIR Configuration
    fhir_version: str = Field(default="4.0.1", alias="FHIR_VERSION")
    fhir_base_url: Optional[str] = Field(default=None, alias="FHIR_BASE_URL")
    
    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="json", alias="LOG_FORMAT")
    
    @property
    def max_file_size_bytes(self) -> int:
        """Convert MB to bytes"""
        return self.max_file_size_mb * 1024 * 1024
    
    @property
    def async_threshold_bytes(self) -> int:
        """Convert MB to bytes for async threshold"""
        return self.async_threshold_mb * 1024 * 1024
    
    def create_directories(self) -> None:
        """Create necessary directories if they don't exist"""
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.result_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
