import pytest
from httpx import AsyncClient
from sqlalchemy import select
from datetime import timedelta

from app.models.user import User, Organization
from app.core.security import create_access_token

pytestmark = pytest.mark.asyncio

async def test_signup_success(async_client: AsyncClient, db_session):
    response = await async_client.post(
        "/api/v1/auth/signup",
        json={
            "name": "New Doctor",
            "email": "newdoc_signup@example.com",
            "password": "Password123!",
            "role": "doctor"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert "token" in data
    
    result = await db_session.execute(select(User).where(User.email == "newdoc_signup@example.com"))
    user = result.scalar_one_or_none()
    assert user is not None
    assert user.account_status == "pending_onboarding"
    assert user.auth_provider == "email"

async def test_signup_duplicate_email(async_client: AsyncClient, doctor_user):
    response = await async_client.post(
        "/api/v1/auth/signup",
        json={
            "name": "Duplicate User",
            "email": doctor_user.email,
            "password": "Password123!",
            "role": "doctor"
        }
    )
    assert response.status_code == 400
    assert "already registered" in response.json().get("detail", "").lower()

async def test_signup_missing_password_for_email(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/auth/signup",
        json={
            "name": "No Password",
            "email": "nopass@example.com",
            "password": None, 
            "role": "doctor"
        }
    )
    assert response.status_code in [400, 422]

async def test_onboarding_doctor(async_client: AsyncClient, db_session):
    res = await async_client.post(
        "/api/v1/auth/signup",
        json={
            "name": "Pending Doctor",
            "email": "pendingdoc@example.com",
            "password": "Password123!",
            "role": "doctor"
        }
    )
    token = res.json()["token"]
    
    response = await async_client.post(
        "/api/v1/auth/onboarding/doctor",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "password": "NewStrongPass1!",
            "confirm_password": "NewStrongPass1!",
            "specialty": "Cardiology",
            "license_number": "LIC123"
        }
    )
    assert response.status_code == 200
    
    result = await db_session.execute(select(User).where(User.email == "pendingdoc@example.com"))
    user = result.scalar_one_or_none()
    assert user.account_status == "active"
    assert user.specialty == "Cardiology"

async def test_onboarding_hospital(async_client: AsyncClient, db_session):
    res = await async_client.post(
        "/api/v1/auth/signup",
        json={
            "name": "Pending Hospital",
            "email": "pendinghosp@example.com",
            "password": "Password123!",
            "role": "hospital"
        }
    )
    token = res.json()["token"]
    
    response = await async_client.post(
        "/api/v1/auth/onboarding/hospital",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "password": "NewStrongPass1!",
            "confirm_password": "NewStrongPass1!",
            "organization_name": "General Hospital"
        }
    )
    assert response.status_code == 200
    
    result = await db_session.execute(select(User).where(User.email == "pendinghosp@example.com"))
    user = result.scalar_one_or_none()
    assert user.account_status == "active"

async def test_onboarding_password_mismatch(async_client: AsyncClient):
    res = await async_client.post("/api/v1/auth/signup", json={
        "name": "Pending Doc Mismatch", 
        "email": "mismatch@example.com", 
        "password": "Password123!", 
        "role": "doctor"
    })
    token = res.json()["token"]
    
    response = await async_client.post(
        "/api/v1/auth/onboarding/doctor",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "password": "NewStrongPass1!",
            "confirm_password": "DifferentPass1!",
            "specialty": "Cardiology"
        }
    )
    assert response.status_code == 422 

async def test_onboarding_invalid_token(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/auth/onboarding/doctor",
        headers={"Authorization": "Bearer invalid_token"},
        json={
            "password": "NewStrongPass1!",
            "confirm_password": "NewStrongPass1!"
        }
    )
    assert response.status_code == 401

async def test_login_restrictions(async_client: AsyncClient):
    await async_client.post("/api/v1/auth/signup", json={
        "name": "Login Test", 
        "email": "logintest@example.com", 
        "password": "Password123!", 
        "role": "doctor"
    })
    
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "logintest@example.com", "password": "Password123!"}
    )
    assert response.status_code == 403
    assert "complete onboarding" in response.json().get("detail", "").lower()

async def test_oauth_role_selection(async_client: AsyncClient, db_session):
    org = Organization(name="OAuth Org")
    db_session.add(org)
    await db_session.flush()
    
    user = User(
        email="oauth_test@example.com",
        full_name="OAuth User",
        role="doctor",
        organization_id=org.id,
        email_verified=True,
        account_status="pending_onboarding",
        auth_provider="google"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    temp_token = create_access_token(
        data={"sub": str(user.id), "email": user.email}, 
        token_type="temp", 
        expires_delta=timedelta(minutes=15)
    )
    
    response = await async_client.post(
        "/api/v1/auth/google/select-role",
        json={
            "role": "hospital",
            "temp_token": temp_token
        }
    )
    assert response.status_code == 200
    assert "token" in response.json()
    
    await db_session.refresh(user)
    assert user.role == "hospital"
    
async def test_oauth_role_selection_invalid_token(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/auth/google/select-role",
        json={
            "role": "hospital",
            "temp_token": "invalid_temp_token"
        }
    )
    assert response.status_code == 401
