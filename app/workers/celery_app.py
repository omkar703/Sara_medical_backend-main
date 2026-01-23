"""Celery Workers and Background Tasks"""

from celery import Celery

from app.config import settings

# Create Celery app
celery_app = Celery(
    "saramedico",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Configure Celery
celery_app.conf.update(
    task_serializer=settings.CELERY_TASK_SERIALIZER,
    accept_content=[settings.CELERY_ACCEPT_CONTENT],
    result_serializer=settings.CELERY_TASK_SERIALIZER,
    timezone=settings.CELERY_TIMEZONE,
    enable_utc=True,
    task_track_started=True,
    task_time_limit=1800,  # 30 minutes max
)

# Auto-discover tasks
celery_app.autodiscover_tasks(['app.workers'])
