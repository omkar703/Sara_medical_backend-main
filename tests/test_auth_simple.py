
import pytest
from httpx import AsyncClient

# Test data
REGISTER_DATA = {
    "email": "integration_test@saramedico.com",
    "password": "Password123",
    "confirm_password": "Password123",
    "first_name": "Test",
    "last_name": "User",
    "role": "patient",
    "organization_name": "Integration Org"
}

LOGIN_DATA = {
    "email": "integration_test@saramedico.com",
    "password": "Password123"
}

@pytest.mark.asyncio
async def test_auth_flow_no_mfa(async_client: AsyncClient):
    # 1. Register a new user
    response = await async_client.post("/api/v1/auth/register", json=REGISTER_DATA)
    if response.status_code == 400 and "Email already registered" in response.text:
        # If user exists from previous run, try login directly
        pass
    else:
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == REGISTER_DATA["email"]
        assert data["email_verified"] is True  # Should be auto-verified now
        assert data["mfa_enabled"] is False

    # 2. Login
    response = await async_client.post("/api/v1/auth/login", json=LOGIN_DATA)
    assert response.status_code == 200
    data = response.json()
    
    # Check if we got tokens directly (MFA bypassed)
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == LOGIN_DATA["email"]
