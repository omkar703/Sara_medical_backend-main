"""
Pydantic Data Models and Schemas
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# Enums
class TaskStatus(str, Enum):
    """Background task status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class OutputFormat(str, Enum):
    """Output format options"""
    JSON = "json"
    FHIR = "fhir"


class EntityType(str, Enum):
    """Medical entity types"""
    PATIENT_NAME = "patient_name"
    PATIENT_AGE = "patient_age"
    PATIENT_GENDER = "patient_gender"
    PATIENT_ID = "patient_id"
    MEDICATION = "medication"
    DOSAGE = "dosage"
    FREQUENCY = "frequency"
    VITAL_SIGN = "vital_sign"
    LAB_VALUE = "lab_value"
    DATE = "date"
    DIAGNOSIS = "diagnosis"


# Response Models
class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Overall health status")
    redis: str = Field(..., description="Redis connection status")
    celery: str = Field(..., description="Celery worker status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ServiceInfoResponse(BaseModel):
    """Root endpoint response"""
    service: str = Field(default="Medical OCR Extraction API")
    version: str = Field(default="1.0.0")
    mode: str = Field(default="cpu-only")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Medical Entity Models
class MedicalEntity(BaseModel):
    """Extracted medical entity"""
    entity_type: EntityType = Field(..., description="Type of medical entity")
    value: str = Field(..., description="Extracted value")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    location: Optional[Dict[str, int]] = Field(None, description="Location in text (line, position)")
    normalized_value: Optional[str] = Field(None, description="Normalized value")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    
    class Config:
        json_schema_extra = {
            "example": {
                "entity_type": "medication",
                "value": "Metformin 500mg",
                "confidence": 0.95,
                "location": {"line": 5, "char_start": 120},
                "normalized_value": "metformin",
                "unit": "mg"
            }
        }


class PageResult(BaseModel):
    """OCR result for a single page"""
    page_number: int = Field(..., description="Page number (1-indexed)")
    text: str = Field(..., description="Extracted text")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Average confidence")
    entities: List[MedicalEntity] = Field(default_factory=list)


# OCR Request/Response Models
class OCRResponse(BaseModel):
    """OCR extraction response"""
    task_id: Optional[str] = Field(None, description="Task ID if async")
    status: str = Field(..., description="Processing status")
    file_name: str = Field(..., description="Original filename")
    pages: Optional[List[PageResult]] = Field(None, description="Page-wise results")
    entities: Optional[List[MedicalEntity]] = Field(None, description="All extracted entities")
    overall_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    processing_time_ms: Optional[float] = Field(None, description="Processing time in milliseconds")
    output_format: OutputFormat = Field(default=OutputFormat.JSON)
    fhir_bundle: Optional[Dict[str, Any]] = Field(None, description="FHIR bundle if requested")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "completed",
                "file_name": "prescription.pdf",
                "pages": [
                    {
                        "page_number": 1,
                        "text": "Patient: John Doe...",
                        "confidence": 0.92,
                        "entities": []
                    }
                ],
                "overall_confidence": 0.92,
                "processing_time_ms": 1234.5,
                "output_format": "json"
            }
        }


class BatchFileInfo(BaseModel):
    """Information about a file in a batch"""
    file_name: str
    file_size: int
    task_id: str


class BatchUploadResponse(BaseModel):
    """Batch upload response"""
    batch_id: str = Field(..., description="Unique batch identifier")
    status: str = Field(..., description="Batch status")
    files: List[BatchFileInfo] = Field(..., description="Files in the batch")
    total_files: int = Field(..., description="Total number of files")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "batch_id": "batch-123e4567-e89b-12d3",
                "status": "queued",
                "files": [
                    {
                        "file_name": "file1.pdf",
                        "file_size": 1024000,
                        "task_id": "task-abc123"
                    }
                ],
                "total_files": 3
            }
        }


class TaskStatusResponse(BaseModel):
    """Background task status response"""
    task_id: str = Field(..., description="Task identifier")
    status: TaskStatus = Field(..., description="Current task status")
    progress: int = Field(..., ge=0, le=100, description="Progress percentage")
    result: Optional[OCRResponse] = Field(None, description="Result if completed")
    error: Optional[str] = Field(None, description="Error message if failed")
    created_at: Optional[datetime] = Field(None)
    started_at: Optional[datetime] = Field(None)
    completed_at: Optional[datetime] = Field(None)
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "task-123e4567",
                "status": "completed",
                "progress": 100,
                "result": {"status": "completed", "file_name": "test.pdf"}
            }
        }


# Validation Models
class FileValidation(BaseModel):
    """File validation result"""
    is_valid: bool
    error: Optional[str] = None
    file_size: int
    file_type: str


# FHIR Models
class FHIRResource(BaseModel):
    """Generic FHIR resource wrapper"""
    resource_type: str = Field(..., description="FHIR resource type")
    id: str = Field(..., description="Resource ID")
    data: Dict[str, Any] = Field(..., description="FHIR resource data")
    
    @field_validator('resource_type')
    @classmethod
    def validate_resource_type(cls, v: str) -> str:
        valid_types = [
            "Patient", "Observation", "MedicationStatement",
            "DiagnosticReport", "Bundle", "Condition"
        ]
        if v not in valid_types:
            raise ValueError(f"Invalid FHIR resource type: {v}")
        return v
