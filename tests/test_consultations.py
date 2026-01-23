
import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_schedule_consultation(
    async_client: AsyncClient,
    doctor_token: str,
    patient_id: str,
    db_session: AsyncSession
):
    """Test scheduling a consultation (creates Zoom meeting)"""
    # Schedule for tomorrow
    scheduled_time = datetime.utcnow() + timedelta(days=1)
    
    response = await async_client.post(
        "/api/v1/consultations",
        headers={"Authorization": f"Bearer {doctor_token}"},
        json={
            "patientId": patient_id,
            "scheduledAt": scheduled_time.isoformat(),
            "durationMinutes": 30,
            "notes": "Initial consultation"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "scheduled"
    assert data["patientId"] == patient_id
    # Check mock meeting data was populated
    assert data["meetingId"] is not None
    assert "zoom.us" in data["joinUrl"]

    return data["id"]


@pytest.mark.asyncio
async def test_list_consultations(
    async_client: AsyncClient,
    doctor_token: str,
    patient_id: str
):
    """Test listing consultations"""
    # Setup: Create a consultation first (reusing logic or endpoint)
    # We rely on previous tests or just create one here
    scheduled_time = datetime.utcnow() + timedelta(days=2)
    await async_client.post(
        "/api/v1/consultations",
        headers={"Authorization": f"Bearer {doctor_token}"},
        json={
            "patientId": patient_id,
            "scheduledAt": scheduled_time.isoformat(),
            "durationMinutes": 45
        }
    )
    
    response = await async_client.get(
        "/api/v1/consultations",
        headers={"Authorization": f"Bearer {doctor_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    assert len(data["consultations"]) > 0


@pytest.mark.asyncio
async def test_get_consultation(
    async_client: AsyncClient,
    doctor_token: str,
    patient_id: str
):
    """Test getting a single consultation"""
    # Create
    scheduled_time = datetime.utcnow() + timedelta(days=3)
    create_resp = await async_client.post(
        "/api/v1/consultations",
        headers={"Authorization": f"Bearer {doctor_token}"},
        json={
            "patientId": patient_id,
            "scheduledAt": scheduled_time.isoformat(),
            "durationMinutes": 15
        }
    )
    cons_id = create_resp.json()["id"]
    
    # Get
    response = await async_client.get(
        f"/api/v1/consultations/{cons_id}",
        headers={"Authorization": f"Bearer {doctor_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == cons_id
    assert data["durationMinutes"] == 15


@pytest.mark.asyncio
async def test_update_consultation(
    async_client: AsyncClient,
    doctor_token: str,
    patient_id: str
):
    """Test updating consultation status/notes"""
    # Create
    scheduled_time = datetime.utcnow() + timedelta(days=4)
    create_resp = await async_client.post(
        "/api/v1/consultations",
        headers={"Authorization": f"Bearer {doctor_token}"},
        json={
            "patientId": patient_id,
            "scheduledAt": scheduled_time.isoformat(),
            "durationMinutes": 30
        }
    )
    cons_id = create_resp.json()["id"]
    
    # Update
    response = await async_client.put(
        f"/api/v1/consultations/{cons_id}",
        headers={"Authorization": f"Bearer {doctor_token}"},
        json={
            "status": "completed",
            "notes": "Updated notes after visit",
            "diagnosis": "Healthy"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["notes"] == "Updated notes after visit"
    assert data["diagnosis"] == "Healthy"


@pytest.mark.asyncio
async def test_analyze_consultation_stub(
    async_client: AsyncClient,
    doctor_token: str,
    patient_id: str
):
    """Test AI analysis stub endpoint"""
    # Create
    scheduled_time = datetime.utcnow() + timedelta(days=5)
    create_resp = await async_client.post(
        "/api/v1/consultations",
        headers={"Authorization": f"Bearer {doctor_token}"},
        json={
            "patientId": patient_id,
            "scheduledAt": scheduled_time.isoformat(),
            "durationMinutes": 30
        }
    )
    cons_id = create_resp.json()["id"]
    
    # Analyze
    response = await async_client.post(
        f"/api/v1/consultations/{cons_id}/analyze",
        headers={"Authorization": f"Bearer {doctor_token}"}
    )
    
    assert response.status_code == 200
    assert "queued" in response.json()["message"]
