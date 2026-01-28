import base64
import httpx
from datetime import datetime
from typing import Dict, Optional
from app.config import settings

class ZoomService:
    """
    Zoom Service for Server-to-Server OAuth integration.
    Handles token management and meeting creation.
    """
    def __init__(self):
        self.client_id = settings.ZOOM_CLIENT_ID
        self.client_secret = settings.ZOOM_CLIENT_SECRET
        self.account_id = settings.ZOOM_ACCOUNT_ID
        self.auth_url = settings.ZOOM_AUTH_URL
        self.base_url = settings.ZOOM_BASE_URL

    async def get_access_token(self) -> str:
        """
        Get access token using Server-to-Server OAuth
        """
        auth_header = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()
        
        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        params = {
            "grant_type": "account_credentials",
            "account_id": self.account_id
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(self.auth_url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            return data["access_token"]

    async def create_meeting(self, topic: str, start_time: str, duration_minutes: int = 30, agenda: str = "") -> Dict:
        """
        Create a new Zoom meeting (Mocked for local audit if credentials missing or forced)
        """
        import os
        if os.getenv("FORCE_MOCK_ZOOM") == "true" or not self.client_id or self.client_id == "your_client_id":
            return {
                "id": "mock_meeting_id",
                "topic": topic,
                "join_url": "https://zoom.us/j/mock",
                "start_url": "https://zoom.us/s/mock",
                "password": "mock_password"
            }

        token = await self.get_access_token()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        meeting_data = {
            "topic": topic,
            "type": 2,  # Scheduled meeting
            "start_time": start_time,
            "duration": duration_minutes,
            "timezone": "UTC",
            "settings": {
                "host_video": True,
                "participant_video": True,
                "join_before_host": False,
                "mute_upon_entry": True,
                "waiting_room": True
            }
        }
        
        # We use the admin email as the host or 'me' if it's the account owner
        user_id = settings.ZOOM_ADMIN_EMAIL
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/users/{user_id}/meetings",
                headers=headers,
                json=meeting_data
            )
            response.raise_for_status()
            return response.json()

# Global instance
zoom_service = ZoomService()
