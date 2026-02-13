"""Voice Verification Endpoints"""

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.deps import get_current_active_user, get_db
from app.core.security import create_voice_token, decode_token
from app.models.user import User
from app.services.voice_service import voice_service

router = APIRouter(prefix="/voice", tags=["Voice Verification"])

# ----------------------------------------------------------------
# 1. HTTP Endpoint: Get WebSocket Token
# ----------------------------------------------------------------

@router.post("/token")
async def get_voice_verification_token(
    current_user: User = Depends(get_current_active_user)
):
    """
    Generate a short-lived token for WebSocket connection.
    This ensures the WebSocket is authenticated without exposing the main access token.
    """
    token = create_voice_token(user_id=str(current_user.id), role=current_user.role)
    
    return {
        "voice_token": token,
        "expires_in": "120 seconds",
        "target_phrase": "Audio test for saramedico audio" # Send target to frontend so user knows what to say
    }


# ----------------------------------------------------------------
# 2. WebSocket Endpoint: Stream Audio & Verify
# ----------------------------------------------------------------

@router.websocket("/ws/verify")
async def websocket_voice_endpoint(websocket: WebSocket, token: str):
    await websocket.accept()

    # --- A. Validation Phase ---
    try:
        payload = decode_token(token)
        if not payload or payload.get("type") != "voice_socket":
            await websocket.close(code=4003)
            return
            
        user_id = payload.get("sub")
        user_role = payload.get("role")
        
    except Exception:
        await websocket.close(code=4003)
        return

    # --- B. Processing Phase ---
    try:
        await websocket.send_json({"status": "ready", "message": "Listening..."})
        
        while True:
            # 1. Receive Audio
            audio_data = await websocket.receive_bytes()
            
            # 2. Store Audio (Async Fire-and-Forget or Await)
            # We await it here to ensure it saves, but in high-load you might use a background task
            stored_path = await voice_service.store_audio_log(
                user_id=user_id,
                role=user_role,
                audio_data=audio_data
            )
            
            # 3. Process & Verify
            transcription = await voice_service.process_audio_chunk(audio_data)
            result = voice_service.verify_speech(transcription, "Audio test for saramedico audio")
            
            # 4. Respond
            response = {
                "status": "success" if result["match"] else "fail",
                "transcription": result["transcription"],
                "confidence": result["score"],
                "audio_reference": stored_path # Return the path so frontend knows it was saved
            }
            
            if not result["match"]:
                 response["message"] = f"No match. You said: '{result['transcription']}'"

            await websocket.send_json(response)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WS Error: {e}")