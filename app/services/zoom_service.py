import base64
import httpx
from datetime import datetime
from typing import Dict, Optional
from app.config import settings

class ZoomService:
    """
    Zoom Service for Server-to-Server OAuth integration.
    Handles token management, meeting creation, and transcript retrieval.
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
        Create a new Zoom meeting
        """
        # Mock logic (keep existing mock check if needed)
        import os
        if os.getenv("FORCE_MOCK_ZOOM") == "true":
            return {
                "id": "mock_meeting_id",
                "join_url": "https://zoom.us/j/mock",
                "start_url": "https://zoom.us/s/mock",
                "password": "mock"
            }

        token = await self.get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        meeting_data = {
            "topic": topic,
            "type": 2, 
            "start_time": str(start_time),
            "duration": duration_minutes,
            "timezone": "UTC",
            "settings": {
                "host_video": True,
                "participant_video": True,
                "auto_recording": "cloud", # FORCE CLOUD RECORDING FOR TRANSCRIPTS
                "waiting_room": True
            }
        }
        
        user_id = settings.ZOOM_ADMIN_EMAIL
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/users/{user_id}/meetings",
                headers=headers,
                json=meeting_data
            )
            response.raise_for_status()
            return response.json()

    async def get_meeting_transcript(self, meeting_id: str) -> Optional[str]:
        """
        Fetch the transcript content for a specific meeting.
        Returns the text content of the transcript or None if not found/ready.
        """
        token = await self.get_access_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        async with httpx.AsyncClient() as client:
            # 1. Get Recording Details
            try:
                response = await client.get(
                    f"{self.base_url}/meetings/{meeting_id}/recordings",
                    headers=headers
                )
                if response.status_code == 404:
                    return None # Recording not processed yet
                response.raise_for_status()
                data = response.json()
            except httpx.HTTPStatusError:
                return None

            # 2. Find the Transcript File
            transcript_file = None
            for file in data.get("recording_files", []):
                if file.get("file_type") == "TRANSCRIPT":
                    transcript_file = file
                    break
            
            if not transcript_file:
                return None

            # 3. Download the content
            download_url = transcript_file.get("download_url")
            if not download_url:
                return None

            # Zoom requires the token in the query param or header for download
            # Using header is safer
            download_response = await client.get(download_url, headers=headers)
            
            if download_response.status_code == 200:
                return download_response.text
            
            return None

zoom_service = ZoomService()