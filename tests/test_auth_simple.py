
import pytest
from httpx import AsyncClient

# Test data
REGISTER_DATA = {
    "email": "integration_test_v3@saramedico.com",
    "password": "Password123!",
    "confirm_password": "Password123!",
    "full_name": "Integration User",
    "role": "doctor",
    "organization_name": "Integration Org",
    "date_of_birth": "1990-01-01",
    "phone_number": "+16502530000"
}

LOGIN_DATA = {
    "email": "integration_test_v3@saramedico.com",
    "password": "Password123!"
}

@pytest.mark.asyncio
async def test_auth_flow_no_mfa(async_client: AsyncClient, db_session):
    from sqlalchemy import select
    from app.models.user import User
    
    # 1. Register a new user
    response = await async_client.post("/api/v1/auth/register", json=REGISTER_DATA)
    if response.status_code == 400 and "Email already registered" in response.text:
        # If user exists from previous run, try login directly
        pass
    else:
        assert response.status_code in [201, 303]
        if response.status_code == 201:
            data = response.json()
            assert data["email"] == REGISTER_DATA["email"]
            assert data["email_verified"] is True  # Should be auto-verified now
            assert data["mfa_enabled"] is False

    # Verify user exists in DB
    result = await db_session.execute(select(User).where(User.email == REGISTER_DATA["email"]))
    user = result.scalar_one_or_none()
    if not user:
        print(f"User {REGISTER_DATA['email']} NOT found in DB after registration!")
    else:
        print(f"User found in DB: {user.email}")

    # 2. Login
    response = await async_client.post("/api/v1/auth/login", json=LOGIN_DATA)
    if response.status_code != 200:
        print(f"Login failed: {response.status_code} - {response.text}")
    assert response.status_code == 200
    data = response.json()
    
    # Check if we got tokens directly (MFA bypassed)
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == LOGIN_DATA["email"]
