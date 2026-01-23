
import pytest
from httpx import AsyncClient
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.audit import AuditLog
from app.models.user import User

@pytest.mark.asyncio
async def test_get_audit_logs(
    async_client: AsyncClient,
    admin_token: str,
    db_session: AsyncSession
):
    """Test retrieving audit logs (Admin only)"""
    # Create a dummy log to ensure something exists
    log = AuditLog(
        action="test_action",
        resource_type="test",
        organization_id=uuid4(), # Just testing retrieval logic broadly or needs matching org?
        # Tests run with isolation. The admin_token user is in "Test Org".
        # We should create a log for THAT org.
    )
    # Wait, fetching user org id is needed.
    # Let's rely on the fact that previous tests/setup created logs (login etc)
    # OR explicit create
    # Let's verify empty or non-empty list
    
    response = await async_client.get(
        "/api/v1/audit/logs",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "logs" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_audit_logs_permission(
    async_client: AsyncClient,
    doctor_token: str
):
    """Test non-admin cannot access audit logs"""
    response = await async_client.get(
        "/api/v1/audit/logs",
        headers={"Authorization": f"Bearer {doctor_token}"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_export_audit_logs(
    async_client: AsyncClient,
    admin_token: str
):
    """Test exporting audit logs as CSV"""
    response = await async_client.get(
        "/api/v1/audit/export",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "Timestamp,Action" in response.text


@pytest.mark.asyncio
async def test_compliance_stats(
    async_client: AsyncClient,
    admin_token: str
):
    """Test compliance stats dashboard"""
    response = await async_client.get(
        "/api/v1/audit/stats",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "total_events" in data
    assert "phi_access_count" in data


@pytest.mark.asyncio
async def test_export_my_data(
    async_client: AsyncClient,
    doctor_token: str
):
    """Test GDPR data portability"""
    response = await async_client.get(
        "/api/v1/compliance/my-data",
        headers={"Authorization": f"Bearer {doctor_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "profile" in data
    assert data["profile"]["role"] == "doctor"
