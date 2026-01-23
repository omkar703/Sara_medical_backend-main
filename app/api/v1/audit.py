"""Audit & Compliance API Endpoints"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user, get_organization_id, require_role
from app.database import get_db
from app.models.user import User
from app.schemas.audit import AuditLogListResponse, AuditLogResponse, ComplianceReport
from app.schemas.document import MessageResponse
from app.services.audit_service import generate_csv_export, get_audit_logs, get_compliance_stats, log_action
from app.services.compliance_service import ComplianceService

# Router 1: Audit (Admin only)
audit_router = APIRouter(prefix="/audit", tags=["Audit"])

@audit_router.get("/logs", response_model=AuditLogListResponse)
async def list_audit_logs(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    user_id: Optional[UUID] = Query(None),
    action: Optional[str] = Query(None),
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(require_role("admin")),
    organization_id: UUID = Depends(get_organization_id),
    db: AsyncSession = Depends(get_db),
):
    """
    View audit logs (Admin only)
    """
    logs, total = await get_audit_logs(
        db, organization_id, start_date, end_date, user_id, action, limit, offset
    )
    
    # Audit this access! (Meta-audit)
    await log_action(
        db, current_user.id, organization_id, "view_audit_logs", "audit_log", None
    )
    await db.commit()
    
    return AuditLogListResponse(logs=logs, total=total)


@audit_router.get("/export")
async def export_audit_logs(
    current_user: User = Depends(require_role("admin")),
    organization_id: UUID = Depends(get_organization_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Download audit logs as CSV
    """
    # Fetch all recent (limit 1000 for safety in MVP)
    logs, _ = await get_audit_logs(db, organization_id, limit=1000)
    
    csv_content = generate_csv_export(logs)
    
    await log_action(
        db, current_user.id, organization_id, "export_audit_logs", "audit_log", None
    )
    await db.commit()
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=audit_logs_{datetime.utcnow().date()}.csv"}
    )


@audit_router.get("/stats", response_model=ComplianceReport)
async def get_stats(
    current_user: User = Depends(require_role("admin")),
    organization_id: UUID = Depends(get_organization_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Get compliance dashboard stats
    """
    stats = await get_compliance_stats(db, organization_id)
    return ComplianceReport(**stats, generated_at=datetime.utcnow())


# Router 2: Compliance (User facing)
compliance_router = APIRouter(prefix="/compliance", tags=["Compliance"])

@compliance_router.get("/my-data")
async def download_my_data(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    GDPR Portability: Download all my data
    """
    service = ComplianceService(db)
    data = await service.export_my_data(current_user.id)
    
    await log_action(
        db, current_user.id, current_user.organization_id, "export_my_data", "user", current_user.id
    )
    await db.commit()
    
    return data


@compliance_router.delete("/my-account", response_model=MessageResponse)
async def delete_my_account(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    GDPR Right to be Forgotten: Request account deletion
    """
    service = ComplianceService(db)
    await service.delete_account(current_user.id)
    
    await log_action(
        db, current_user.id, current_user.organization_id, "delete_account", "user", current_user.id
    )
    await db.commit()
    
    return MessageResponse(message="Account scheduled for deletion. You have been logged out.")
