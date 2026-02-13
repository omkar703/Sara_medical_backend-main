"""Health Metric Model for Vitals (BP, Heart Rate, etc.)"""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base

class HealthMetric(Base):
    __tablename__ = "health_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Link to Patient
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Metric Details
    metric_type = Column(String(50), nullable=False)  # e.g., "blood_pressure", "heart_rate"
    value = Column(String(50), nullable=False)        # e.g., "120/80", "72"
    unit = Column(String(20), nullable=True)          # e.g., "mmHg", "bpm"
    
    # Metadata
    recorded_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    notes = Column(String(255), nullable=True)

    # Relationships
    patient = relationship("Patient", backref="health_metrics")

    def __repr__(self):
        return f"<HealthMetric {self.metric_type}: {self.value}>"