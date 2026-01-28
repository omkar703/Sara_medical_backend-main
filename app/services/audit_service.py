"""Audit Log Service"""

from datetime import datetime
from uuid import UUID

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog


async def log_action(
    db: AsyncSession,
    user_id: UUID | None,
    organization_id: UUID | None,
    action: str,
    resource_type: str,
    resource_id: UUID | None,
    request: Request | None = None,
    metadata: dict | None = None,
) -> AuditLog:
    """
    Create an audit log entry for HIPAA compliance
    
    Args:
        db: Database session
        user_id: ID of the user performing the action
        organization_id: ID of the organization
        action: Action performed (create, read, update, delete)
        resource_type: Type of resource accessed (e.g., patient, document)
        resource_id: ID of the resource
        request: FastAPI request object (for IP/User-Agent extraction)
        metadata: Additional context details
        
    Returns:
        Created AuditLog entry
    """
    ip_address = None
    user_agent = None

    if request:
        if request.client:
            ip_address = request.client.host
        user_agent = request.headers.get("user-agent")

    audit_log = AuditLog(
        user_id=user_id,
        organization_id=organization_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        user_agent=user_agent,
        metadata_=metadata,
        timestamp=datetime.utcnow()
    )

    db.add(audit_log)
    # Note: We don't commit here to allow the caller to include this in their transaction
    # or commit independently. For most safe auditing, this should be committed even if
    # the main operation fails, but typically we want it part of the same transaction
    # for data integrity.
    
    return audit_log


async def get_audit_logs(
    db: AsyncSession,
    organization_id: UUID,
    start_date: datetime = None,
    end_date: datetime = None,
    user_id: UUID = None,
    action: str = None,
    limit: int = 100,
    offset: int = 0
) -> (list[AuditLog], int):
    """
    Fetch filtered audit logs
    """
    from sqlalchemy import select, func, and_
    
    query = select(AuditLog).where(AuditLog.organization_id == organization_id)
    
    if start_date:
        query = query.where(AuditLog.timestamp >= start_date)
    if end_date:
        query = query.where(AuditLog.timestamp <= end_date)
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    if action:
        query = query.where(AuditLog.action == action)
        
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()
    
    # Apply pagination
    query = query.order_by(AuditLog.timestamp.desc()).limit(limit).offset(offset)
    
    result = await db.execute(query)
    return result.scalars().all(), total


def generate_csv_export(logs: list[AuditLog]) -> str:
    """
    Generate CSV string from logs
    """
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow([
        "Timestamp", "Action", "User ID", "Resource Type", "Resource ID", 
        "IP Address", "User Agent", "Metadata"
    ])
    
    for log in logs:
        writer.writerow([
            log.timestamp.isoformat(),
            log.action,
            str(log.user_id) if log.user_id else "System",
            log.resource_type,
            str(log.resource_id) if log.resource_id else "",
            str(log.ip_address) if log.ip_address else "",
            log.user_agent or "",
            str(log.metadata_) if log.metadata_ else ""
        ])
        
    return output.getvalue()


async def get_compliance_stats(
    db: AsyncSession,
    organization_id: UUID,
    days: int = 30
) -> dict:
    """
    Get compliance statistics for the last N days
    """
    from sqlalchemy import select, func
    from datetime import timedelta
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Base query
    base_query = select(AuditLog).where(
        AuditLog.organization_id == organization_id,
        AuditLog.timestamp >= start_date
    )
    
    # Total events
    count_query = select(func.count()).select_from(base_query.subquery())
    total_events = (await db.execute(count_query)).scalar_one()
    
    # PHI Access (view/export/download of patients/documents)
    # Using simple string matching on action/resource for MVP
    phi_query = select(func.count()).select_from(AuditLog).where(
        AuditLog.organization_id == organization_id,
        AuditLog.timestamp >= start_date,
        AuditLog.resource_type.in_(["patient", "document", "consultation"]),
        AuditLog.action.in_(["view", "download", "export"])
    )
    phi_count = (await db.execute(phi_query)).scalar_one()
    
    # Active users count
    users_query = select(func.count(func.distinct(AuditLog.user_id))).where(
        AuditLog.organization_id == organization_id,
        AuditLog.timestamp >= start_date
    )
    users_count = (await db.execute(users_query)).scalar_one()
    
    return {
        "period_start": start_date,
        "period_end": datetime.utcnow(),
        "total_events": total_events,
        "phi_access_count": phi_count,
        "users_active_count": users_count
    }


class AuditService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_event(
        self,
        user_id: UUID | None,
        action: str,
        resource_type: str,
        resource_id: UUID | None,
        organization_id: UUID | None,
        metadata: dict | None = None,
        request: Request | None = None
    ) -> AuditLog:
        return await log_action(
            db=self.db,
            user_id=user_id,
            organization_id=organization_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            request=request,
            metadata=metadata
        )

    async def get_logs(self, *args, **kwargs):
        return await get_audit_logs(self.db, *args, **kwargs)

    async def get_stats(self, *args, **kwargs):
        return await get_compliance_stats(self.db, *args, **kwargs)
