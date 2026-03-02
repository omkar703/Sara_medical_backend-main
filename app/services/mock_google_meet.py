import asyncio
from datetime import datetime
from uuid import uuid4

class MockGoogleMeetService:
    async def create_meeting(self, start_time, duration_minutes, summary, description, attendees):
        print(f"MOCK: Creating Google Meet for {summary}")
        return str(uuid4()), f"https://meet.google.com/mock-{uuid4().hex[:4]}-{uuid4().hex[:4]}"

    async def get_meeting_transcript(self, event_id):
        return "This is a mock transcript of the medical consultation."

google_meet_service = MockGoogleMeetService()
