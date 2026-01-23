
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import Invitation

@pytest.mark.asyncio
async def test_get_my_organization(
    async_client: AsyncClient,
    doctor_token: str
):
    """Test getting organization details"""
    response = await async_client.get(
        "/api/v1/organization",
        headers={"Authorization": f"Bearer {doctor_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "subscription_tier" in data


@pytest.mark.asyncio
async def test_invite_member(
    async_client: AsyncClient,
    admin_token: str
):
    """Test inviting a new member (Admin only)"""
    new_email = "newdoctor@example.com"
    
    response = await async_client.post(
        "/api/v1/organization/invitations",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "email": new_email,
            "role": "doctor"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == new_email
    assert data["status"] == "pending"
    return data["id"]  # Return ID for potential reuse


@pytest.mark.asyncio
async def test_invite_permission(
    async_client: AsyncClient,
    doctor_token: str
):
    """Test non-admin cannot invite"""
    response = await async_client.post(
        "/api/v1/organization/invitations",
        headers={"Authorization": f"Bearer {doctor_token}"},
        json={
            "email": "fail@example.com",
            "role": "doctor"
        }
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_accept_invitation(
    async_client: AsyncClient,
    admin_token: str,
    db_session: AsyncSession
):
    """Test accepting an invitation"""
    # 1. Invite
    invite_email = "accept_me@example.com"
    invite_resp = await async_client.post(
        "/api/v1/organization/invitations",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "email": invite_email,
            "role": "doctor"
        }
    )
    assert invite_resp.status_code == 200
    
    # 2. Get the token from DB (since response doesn't show secret token for security reasons? 
    # Wait, implementation hash 256. 
    # Oh, the SERVICE implementation `invite_member` generates `token` (plain) but stores `token_hash`.
    # And it PRINTS the link.
    # The API returns `InvitationResponse` which usually matches model/schema.
    # The `InvitationResponse` schema includes `id`, `email`, but NOT `token`.
    # In a real integration test, we wouldn't have the token unless we mocked the email service or return it in dev mode.
    # OR, for testing purpose, we need to bypass or peek.
    # BUT, the Service prints it. We can't capture print easily here.
    # HOWEVER, the Service `invite_member` calls `secrets.token_urlsafe(32)`.
    # It returns the `Invitation` object. But the `Invitation` object has `token_hash`, not the plain token.
    # So we cannot clear this test unless we mock `secrets` or changing the return to include token for `dev` env?
    # Or, we manually update the DB record to set a known hash.
    
    # Strategy: Manually update the invitation in DB to have a known hash for a known token.
    import hashlib
    known_token = "test_token_123"
    known_hash = hashlib.sha256(known_token.encode()).hexdigest()
    
    # Find the invitation by email
    result = await db_session.execute(select(Invitation).where(Invitation.email == invite_email))
    invitation = result.scalar_one_or_none()
    assert invitation is not None
    
    invitation.token_hash = known_hash
    await db_session.commit()
    
    # 3. Accept
    accept_resp = await async_client.post(
        "/api/v1/organization/invitations/accept",
        json={
            "token": known_token,
            "full_name": "New Doctor",
            "password": "SecurePassword123!",
            "specialty": "Cardiology"
        }
    )
    
    assert accept_resp.status_code == 200
    data = accept_resp.json()
    assert data["role"] == "doctor"
    assert data["email"] == invite_email


@pytest.mark.asyncio
async def test_list_members(
    async_client: AsyncClient,
    admin_token: str
):
    """Test listing members"""
    response = await async_client.get(
        "/api/v1/organization/members",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1  # At least the admin
    # Verify fields
    assert "full_name" in data[0]
    assert "email" in data[0]
