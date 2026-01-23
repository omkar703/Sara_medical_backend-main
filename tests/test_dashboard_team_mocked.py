import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timedelta
import uuid

# Import the app to get access to routes and dependencies
from app.main import app
from app.database import get_db
from app.core.deps import get_current_user, get_organization_id
from app.models.user import User, Invitation
from app.models.appointment import Appointment
from app.models.activity_log import ActivityLog
from app.models.consultation import Consultation
from app.core.security import PIIEncryption

# Mock PII encryption to avoid real decrypt issues
@pytest.fixture(autouse=True)
def mock_pii():
    with patch("app.core.security.pii_encryption") as mock:
        mock.decrypt.side_effect = lambda x: x if isinstance(x, str) else "Decrypted"
        yield mock

# Mock current user and organization
@pytest.fixture
def mock_user():
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.role = "doctor"
    user.organization_id = uuid.uuid4()
    user.full_name = "Dr. Test"
    return user

@pytest.fixture
def mock_db():
    return AsyncMock()

@pytest.mark.asyncio
async def test_get_next_appointment_success_mocked(mock_user, mock_db):
    # Setup dependency overrides
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: mock_db
    
    # Mock database results
    appointment = MagicMock(spec=Appointment)
    appointment.id = uuid.uuid4()
    appointment.patient_id = uuid.uuid4()
    appointment.requested_date = datetime.utcnow() + timedelta(hours=1)
    appointment.reason = "Post-op check"
    appointment.patient.full_name = "Daniel Benjamin"
    
    # Mock Consultation result for "last_visit"
    consultation = MagicMock(spec=Consultation)
    consultation.scheduled_at = datetime.utcnow() - timedelta(days=10)
    
    # Configure mock execute responses
    # First call is for the appointment query
    # Second call is for the last_visit query
    mock_db.execute.side_effect = [
        MagicMock(scalar_one_or_none=lambda: appointment),
        MagicMock(scalar_one_or_none=lambda: consultation)
    ]
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/doctor/schedule/next")
        
    assert response.status_code == 200
    data = response.json()
    assert data["patient_name"] == "Daniel Benjamin"
    assert data["reason"] == "Post-op check"
    assert data["time"] is not None
    
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_get_activity_feed_mocked(mock_user, mock_db):
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_organization_id] = lambda: mock_user.organization_id
    app.dependency_overrides[get_db] = lambda: mock_db
    
    # Mock activity log list
    log = MagicMock(spec=ActivityLog)
    log.activity_type = "Lab Results Reviewed"
    log.description = "Reviewed labs for John Von"
    log.status = "Completed"
    log.created_at = datetime.utcnow()
    log.extra_data = {}
    
    mock_db.execute.return_value = MagicMock(scalars=lambda: MagicMock(all=lambda: [log]))
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/doctor/activity")
        
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["activity_type"] == "Lab Results Reviewed"
    
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_invite_team_member_mocked(mock_user, mock_db):
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_organization_id] = lambda: mock_user.organization_id
    app.dependency_overrides[get_db] = lambda: mock_db
    
    # Mock duplicate check (none found)
    mock_db.execute.return_value = MagicMock(scalar_one_or_none=lambda: None)
    
    invite_payload = {
        "full_name": "New Nurse",
        "email": "nurse@hospital.com",
        "role": "MEMBER"
    }
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/team/invite", json=invite_payload)
        
    assert response.status_code == 201
    assert response.json()["detail"] == "Invitation sent"
    
    # Verify that an activity log entry would be created
    # The endpoint adds Invitation and ActivityLog to session
    assert mock_db.add.call_count >= 2 
    
    app.dependency_overrides.clear()
