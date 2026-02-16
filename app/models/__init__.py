"""Database Models"""

# Import all models here to ensure they're registered with Base.metadata
# This is required for Alembic's autogenerate feature

from app.models.audit import AuditLog
from app.models.consultation import Consultation
from app.models.document import Document
from app.models.patient import Patient
from app.models.task import Task
from app.models.appointment import Appointment
from app.models.activity_log import ActivityLog
from app.models.calendar_event import CalendarEvent
from app.models.user import Organization, RefreshToken, User

__all__ = ["Organization", "User", "RefreshToken", "Patient", "AuditLog", "Document", "Consultation", "Task", "Appointment", "ActivityLog", "CalendarEvent"]

# Future imports:
# from app.models.document import Document
# from app.models.consultation import Consultation
