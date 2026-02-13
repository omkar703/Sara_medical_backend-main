"""Voice Service for Speech-to-Text, Verification, and Storage"""

import Levenshtein
import speech_recognition as sr
import io
import logging
from datetime import datetime
from uuid import UUID

from app.services.minio_service import minio_service
from app.config import settings

logger = logging.getLogger(__name__)

class VoiceService:
    def __init__(self):
        self.recognizer = sr.Recognizer()

    async def process_audio_chunk(self, audio_data: bytes) -> str:
        """Convert raw audio bytes to text (STT)."""
        try:
            with io.BytesIO(audio_data) as audio_file:
                with sr.AudioFile(audio_file) as source:
                    audio = self.recognizer.record(source)
            
            text = self.recognizer.recognize_google(audio)
            return text.lower()
            
        except sr.UnknownValueError:
            return ""
        except Exception as e:
            logger.error(f"Audio processing error: {e}")
            return ""

    def verify_speech(self, transcribed_text: str, target_text: str) -> dict:
        """Compare transcribed text with target text."""
        if not transcribed_text:
            return {"match": False, "score": 0, "transcription": ""}

        s1 = transcribed_text.strip().lower()
        s2 = target_text.strip().lower()

        distance = Levenshtein.distance(s1, s2)
        max_len = max(len(s1), len(s2))
        similarity = 1 - (distance / max_len)
        
        return {
            "match": similarity >= 0.8,
            "score": round(similarity * 100, 2),
            "transcription": transcribed_text,
            "target": target_text
        }

    async def store_audio_log(self, user_id: str, role: str, audio_data: bytes) -> str:
        """
        Store audio file to MinIO with structured path.
        Structure: {role}s/{user_id}/{timestamp}.wav
        Example: doctors/123-abc/20260213_103000.wav
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. Determine Folder based on Role
        # Handle "doctor", "patient", "admin"
        folder = f"{role}s" # e.g., 'doctors', 'patients'
        
        # 2. Construct Object Name (Path)
        filename = f"{timestamp}.wav"
        object_name = f"{folder}/{user_id}/{filename}"
        
        # 3. Upload using existing MinIOService
        success = minio_service.upload_bytes(
            file_data=audio_data,
            bucket_name=settings.MINIO_BUCKET_AUDIO, # Ensure this is in your config
            object_name=object_name,
            content_type="audio/wav"
        )
        
        if success:
            logger.info(f"✅ Audio log saved: {object_name}")
            return object_name
        else:
            logger.error(f"❌ Failed to save audio log: {object_name}")
            return None

voice_service = VoiceService()