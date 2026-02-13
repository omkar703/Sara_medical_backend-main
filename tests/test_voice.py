import asyncio
import requests
import websockets
import json
import sounddevice as sd
import numpy as np
import io
import scipy.io.wavfile as wav
import sys
import json

# --- CONFIGURATION ---
BASE_URL = "http://localhost:8000/api/v1"
WS_URL = "ws://localhost:8000/api/v1/voice/ws/verify"

# Use a valid doctor/admin email and password from your local DB
EMAIL =  "patient_e2e_final@test.com"
PASSWORD = "Password123"

# Audio Settings
DURATION = 5  # Seconds to record
SAMPLE_RATE = 44100
CHANNELS = 1

def login():
    """1. Authenticate and get the main Access Token"""
    print(f"🔑 Logging in as {EMAIL}...")
    url = f"{BASE_URL}/auth/login"
    payload = {"email": EMAIL, "password": PASSWORD}
    # Send as form-data
    response = requests.post(url, json=payload)
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.text}")
        sys.exit(1)
        
    print("✅ Login successful!")
    return response.json()["access_token"]

def get_voice_token(access_token):
    """2. Request the short-lived Voice Token"""
    print("🎫 Requesting Voice Verification Token...")
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.post(f"{BASE_URL}/voice/token", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Failed to get voice token: {response.text}")
        sys.exit(1)
        
    data = response.json()
    print(f"✅ Received Voice Token")
    print(f"🗣️  TARGET PHRASE: '{data['target_phrase']}'")
    return data["voice_token"]

def record_audio():
    """3. Record audio from microphone and convert to WAV bytes"""
    print(f"\n🎙️  Recording for {DURATION} seconds... Please speak the target phrase!")
    print("   (Recording...)")
    
    # Record raw data
    my_recording = sd.rec(int(DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=CHANNELS, dtype='int16')
    sd.wait()  # Wait until recording is finished
    print("⏹️  Recording finished.")

    # Convert to WAV container (bytes)
    # The backend expects a file-like object with headers, so we wrap it in a WAV container
    wav_buffer = io.BytesIO()
    wav.write(wav_buffer, SAMPLE_RATE, my_recording)
    return wav_buffer.getvalue()

async def send_audio_via_ws(voice_token):
    """4. Connect to WebSocket and send audio"""
    uri = f"{WS_URL}?token={voice_token}"
    
    print(f"\n🔌 Connecting to WebSocket: {uri}")
    
    async with websockets.connect(uri) as websocket:
        # Wait for "ready" message
        response = await websocket.recv()
        print(f"📩 Server says: {response}")
        
        # Record Audio
        audio_bytes = record_audio()
        
        print(f"🚀 Sending {len(audio_bytes)} bytes of audio data...")
        await websocket.send(audio_bytes)
        
        # Wait for result
        print("⏳ Waiting for transcription...")
        result = await websocket.recv()
        result_data = json.loads(result)
        
        print("\n" + "="*30)
        print("🔍 RESULT")
        print("="*30)
        print(f"Status:       {result_data.get('status')}")
        print(f"Transcription: {result_data.get('transcription')}")
        print(f"Confidence:   {result_data.get('confidence')}")
        
        if result_data.get('status') == 'success':
            print("✅ VERIFICATION SUCCESSFUL")
        else:
            print("❌ VERIFICATION FAILED")
            print(f"Message: {result_data.get('message')}")

def main():
    try:
        # Step 1: Login
        access_token = login()
        
        # Step 2: Get Voice Token
        voice_token = get_voice_token(access_token)
        
        # Step 3: Run Async WebSocket Client
        asyncio.run(send_audio_via_ws(voice_token))
        
    except KeyboardInterrupt:
        print("\n👋 Exiting...")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()