import uuid
from datetime import datetime, timedelta
from typing import Tuple, Optional
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.config import settings

class GoogleMeetService:
    def __init__(self):
        scopes = [
            'https://www.googleapis.com/auth/calendar.events',
            'https://www.googleapis.com/auth/calendar.readonly',
            'https://www.googleapis.com/auth/drive.readonly'
        ]
        try:
            self.creds = Credentials(
                token=None,
                refresh_token=settings.GOOGLE_REFRESH_TOKEN,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.GOOGLE_CLIENT_ID,
                client_secret=settings.GOOGLE_CLIENT_SECRET,
                scopes=scopes
            )
            # Build both Calendar and Drive services
            self.calendar_service = build('calendar', 'v3', credentials=self.creds)
            self.drive_service    = build('drive', 'v3', credentials=self.creds)
            self._available = True
        except Exception as e:
            print(f"[GoogleMeetService] ⚠ Could not initialize Google API services: {e}")
            print("[GoogleMeetService] Calendar/Meet features will be unavailable until credentials are configured.")
            self.calendar_service = None
            self.drive_service    = None
            self._available = False

    def _require_service(self):
        """Raise a clear error if Google API is not configured."""
        if not self._available:
            raise RuntimeError(
                "Google API credentials are not configured. "
                "Set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, "
                "and GOOGLE_REFRESH_TOKEN in your .env file."
            )


    async def get_meeting_transcript(self, google_event_id: str) -> Optional[str]:
        """
        Checks the Calendar event for an attached transcript and downloads its text.
        """
        try:
            # 1. Fetch the event to look for attachments
            event = self.calendar_service.events().get(
                calendarId='primary', 
                eventId=google_event_id
            ).execute()
            
            summary = event.get('summary', 'Consultation')
            attachments = event.get('attachments', [])
            transcript_file_id = None
            
            # 2. Primary check: Find the Google Doc attachment linked to the event
            for att in attachments:
                mime_type = att.get('mimeType', '')
                title = att.get('title', '')
                if 'application/vnd.google-apps' in mime_type and 'Transcript' in title:
                    transcript_file_id = att.get('fileId')
                    print(f"[GoogleMeetService] Found transcript attached to event: {title}")
                    break
                    
            # 3. Fallback check: Search Drive for files matching the meeting summary
            if not transcript_file_id:
                print(f"[GoogleMeetService] Transcript not attached to event. Searching Drive for: {summary}")
                # Search for files with the summary in name and 'Transcript'
                # Google naming pattern is usually "[Summary] - [Date] [Time] - Transcript"
                safe_summary = summary.replace("'", "\\'")
                query = f"name contains '{safe_summary}' and name contains 'Transcript' and trashed = false"
                drive_results = self.drive_service.files().list(
                    q=query,
                    pageSize=5,
                    fields="files(id, name, createdTime)",
                    orderBy="createdTime desc"
                ).execute()
                
                drive_files = drive_results.get('files', [])
                if drive_files:
                    # Pick the most recent one
                    transcript_file_id = drive_files[0].get('id')
                    print(f"[GoogleMeetService] Found transcript in Drive search: {drive_files[0].get('name')}")

            if not transcript_file_id:
                print(f"[GoogleMeetService] No transcript found for Event ID {google_event_id}")
                return None 
                
            # 4. Download and export as plain text
            request = self.drive_service.files().export_media(
                fileId=transcript_file_id, 
                mimeType='text/plain'
            )
            transcript_bytes = request.execute()
            
            return transcript_bytes.decode('utf-8')
            
        except Exception as e:
            print(f"Error fetching transcript: {e}")
            return None

    async def create_meeting(
        self, 
        start_time: datetime, 
        duration_minutes: int, 
        summary: str, 
        description: str = "",
        attendees: list[str] = None # NEW PARAMETER
    ) -> Tuple[str, str]:
        
        end_time = start_time + timedelta(minutes=duration_minutes)
        request_id = uuid.uuid4().hex

        event_body = {
            'summary': summary,
            'description': description,
            'start': {'dateTime': start_time.isoformat(), 'timeZone': 'UTC'},
            'end': {'dateTime': end_time.isoformat(), 'timeZone': 'UTC'},
            'conferenceData': {
                'createRequest': {
                    'requestId': request_id,
                    'conferenceSolutionKey': {'type': 'hangoutsMeet'}
                }
            }
        }

        # NEW: Add the attendees to the event body
        if attendees:
            cleaned_attendees = []
            for email in attendees:
                if email:
                    # Strip spaces, newlines, and hidden characters
                    clean_email = str(email).strip().replace("\u200b", "").replace(" ", "")
                    if "@" in clean_email:
                        cleaned_attendees.append({'email': clean_email})
            
            if cleaned_attendees:
                event_body['attendees'] = cleaned_attendees

        # The conferenceDataVersion=1 parameter is REQUIRED to generate the Meet link
        event = self.calendar_service.events().insert(
            calendarId='primary', 
            body=event_body, 
            conferenceDataVersion=1,
            sendUpdates="all"
        ).execute()

        # Extract the ID and the Meet Link from the response
        google_event_id = event.get('id')
        meet_link = event.get('hangoutLink')

        if not meet_link:
            raise ValueError("Failed to generate Google Meet link. Ensure your Google Workspace/Account supports Meet API.")

        return google_event_id, meet_link

# Export a singleton instance
google_meet_service = GoogleMeetService()