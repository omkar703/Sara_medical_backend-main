"""API v1 Routes"""

from fastapi import APIRouter

from app.api.v1 import auth, consultations, documents, organizations, patients, websockets, audit, tasks, doctor, appointments, team

api_router = APIRouter()

# Include all route modules
api_router.include_router(auth.router)
api_router.include_router(patients.router)
api_router.include_router(documents.router)
api_router.include_router(consultations.router)
api_router.include_router(websockets.router)
api_router.include_router(organizations.router)
api_router.include_router(audit.audit_router)
api_router.include_router(audit.compliance_router)
api_router.include_router(tasks.router)
api_router.include_router(doctor.router)
api_router.include_router(appointments.router)
api_router.include_router(team.router)
