import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta
from app.models.appointment import Appointment
from app.models.activity_log import ActivityLog
from app.models.user import User, Invitation

@pytest.mark.asyncio
async def test_get_next_appointment_not_found(async_client: AsyncClient, doctor_token: str):
    headers = {"Authorization": f"Bearer {doctor_token}"}
    response = await async_client.get("/api/v1/doctor/schedule/next", headers=headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "No upcoming appointment found"

@pytest.mark.asyncio
async def test_get_next_appointment_success(async_client: AsyncClient, db_session, test_user: User, doctor_token: str, patient_id: str):
    # Create a confirmed appointment for today
    appointment = Appointment(
        doctor_id=test_user.id,
        patient_id=patient_id,
        requested_date=datetime.utcnow() + timedelta(hours=1),
        reason="Follow-Up",
        status="accepted"
    )
    db_session.add(appointment)
    await db_session.commit()
    await db_session.refresh(appointment)

    headers = {"Authorization": f"Bearer {doctor_token}"}
    response = await async_client.get("/api/v1/doctor/schedule/next", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["appointment_id"] == str(appointment.id)
    assert data["reason"] == "Follow-Up"
    assert data["patient_name"] == "John Doe"

@pytest.mark.asyncio
async def test_get_activity_feed(async_client: AsyncClient, db_session, test_user: User, doctor_token: str):
    # Create an activity log
    log = ActivityLog(
        user_id=test_user.id,
        organization_id=test_user.organization_id,
        activity_type="Lab Results Reviewed",
        description="Reviewed labs for Patient X",
        status="completed"
    )
    db_session.add(log)
    await db_session.commit()

    headers = {"Authorization": f"Bearer {doctor_token}"}
    response = await async_client.get("/api/v1/doctor/activity", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["activity_type"] == "Lab Results Reviewed"

@pytest.mark.asyncio
async def test_team_invitation_flow(async_client: AsyncClient, doctor_token: str, db_session, test_user: User):
    headers = {"Authorization": f"Bearer {doctor_token}"}
    invite_data = {
        "full_name": "New Nurse",
        "email": "nurse@hospital.com",
        "role": "MEMBER"
    }
    
    # 1. Send invite
    response = await async_client.post("/api/v1/team/invite", json=invite_data, headers=headers)
    assert response.status_code == 201
    assert response.json()["detail"] == "Invitation sent"
    
    # 2. Check for duplicate error
    response = await async_client.post("/api/v1/team/invite", json=invite_data, headers=headers)
    assert response.status_code == 400
    assert response.json()["detail"] == "User already invited."
    
    # 3. Check activity feed for the invite
    response = await async_client.get("/api/v1/doctor/activity", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert any(log["activity_type"] == "Team Invite Sent" for log in data)

@pytest.mark.asyncio
async def test_list_team_roles(async_client: AsyncClient, doctor_token: str):
    headers = {"Authorization": f"Bearer {doctor_token}"}
    response = await async_client.get("/api/v1/team/roles", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert any(role["role"] == "ADMINISTRATOR" for role in data)
