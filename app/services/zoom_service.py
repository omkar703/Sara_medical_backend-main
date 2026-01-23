"""Zoom Integration Service"""

import base64
import time
from typing import Dict, Optional

import httpx
from fastapi import HTTPException

from app.config import settings


class ZoomService:
    """Service for interacting with Zoom API"""
    
    _access_token: Optional[str] = None
    _token_expires_at: float = 0
    
    async def get_access_token(self) -> str:
        """
        Get Server-to-Server OAuth access token
        Caching the token until it expires
        """
        if self._access_token and time.time() < self._token_expires_at:
            return self._access_token
        
        # Create Basic Auth header
        auth_string = f"{settings.ZOOM_CLIENT_ID}:{settings.ZOOM_CLIENT_SECRET}"
        b64_auth = base64.b64encode(auth_string.encode()).decode()
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{settings.ZOOM_AUTH_URL}?grant_type=account_credentials&account_id={settings.ZOOM_ACCOUNT_ID}",
                    headers={"Authorization": f"Basic {b64_auth}"}
                )
                response.raise_for_status()
                data = response.json()
                
                self._access_token = data["access_token"]
                # Expires in 1 hour usually, refresh 5 mins early
                self._token_expires_at = time.time() + data["expires_in"] - 300
                
                return self._access_token
            except httpx.HTTPError as e:
                # Log error here or raise specific exception
                print(f"Zoom Auth Error: {str(e)}")
                # For development fallback if creds are invalid
                if settings.APP_ENV == "development":
                    return "mock_zoom_token"
                raise HTTPException(status_code=500, detail="Failed to authenticate with Zoom")
    
    async def create_meeting(
        self,
        topic: str,
        start_time: str,  # ISO8601
        duration_minutes: int,
        agenda: str = ""
    ) -> Dict:
        """
        Create a Zoom meeting
        """
        # For development/testing/demo without real credentials
        if settings.APP_ENV == "development" and not settings.ZOOM_ACCOUNT_ID:
            return self._create_mock_meeting()

        token = await self.get_access_token()
        
        # If we got a mock token (failed auth in dev), return mock meeting
        if token == "mock_zoom_token":
            return self._create_mock_meeting()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "topic": topic,
            "type": 2,  # Scheduled meeting
            "start_time": start_time,
            "duration": duration_minutes,
            "timezone": "UTC",
            "agenda": agenda,
            "settings": {
                "host_video": True,
                "participant_video": True,
                "join_before_host": True,
                "mute_upon_entry": False,
                "waiting_room": False  # Auto-join for smoother experience
            }
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{settings.ZOOM_BASE_URL}/users/me/meetings",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                print(f"Zoom API Error: {str(e)}")
                if settings.APP_ENV == "development":
                    return self._create_mock_meeting()
                raise HTTPException(status_code=500, detail="Failed to create Zoom meeting")
    
    def _create_mock_meeting(self) -> Dict:
        """Return a mock meeting object for dev/test"""
        from uuid import uuid4
        meeting_id = str(int(time.time()))
        return {
            "id": meeting_id,
            "join_url": f"https://zoom.us/j/{meeting_id}?pwd=mock",
            "start_url": f"https://zoom.us/s/{meeting_id}?pwd=mock",
            "password": "mock_password",
        }
