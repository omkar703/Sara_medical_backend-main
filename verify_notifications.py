import asyncio
import uuid
import json
import httpx
import websockets
from sqlalchemy import select
from datetime import timedelta, datetime
from app.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import create_access_token

async def verify_notifications():
    print("--- Notification System Verification (Refined) ---")
    
    async with AsyncSessionLocal() as db:
        # 1. Get a Doctor and a Patient USER for testing
        doctor = (await db.execute(select(User).where(User.role == 'doctor').limit(1))).scalar_one()
        patient_user = (await db.execute(select(User).where(User.role == 'patient').limit(1))).scalar_one()
        
        print(f"Testing with Doctor: {doctor.full_name} ({doctor.id}) [Org: {doctor.organization_id}]")
        print(f"Testing with Patient: {patient_user.full_name} ({patient_user.id}) [Org: {patient_user.organization_id}]")
        
        # 2. Create tokens
        doctor_token = create_access_token(
            data={"sub": str(doctor.id), "role": doctor.role},
            expires_delta=timedelta(minutes=60)
        )
        patient_token = create_access_token(
            data={"sub": str(patient_user.id), "role": patient_user.role},
            expires_delta=timedelta(minutes=60)
        )

    # 3. Connect to WebSocket as Doctor
    # Using 127.0.0.1 and correct path
    ws_url = f"ws://127.0.0.1:8000/api/v1/ws?token={doctor_token}"
    print(f"Connecting to {ws_url}...")
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print("Connected to WebSocket as Doctor.")
            
            # 4. Trigger Notification: Create Appointment as Patient
            async def trigger_appointment():
                await asyncio.sleep(2) # Give it time to be ready
                print("\nTriggering Appointment Request...")
                headers = {"Authorization": f"Bearer {patient_token}"}
                req_data = {
                    "doctor_id": str(doctor.id),
                    "requested_date": (datetime.utcnow() + timedelta(days=1)).isoformat(),
                    "reason": "Test notification system",
                    "grant_access_to_history": False
                }
                async with httpx.AsyncClient() as client:
                    # Using 127.0.0.1 here too
                    resp = await client.post("http://127.0.0.1:8000/api/v1/appointments", headers=headers, json=req_data)
                    if resp.status_code == 201:
                        print("Appointment created successfully.")
                    else:
                        print(f"Failed to create appointment: {resp.status_code} - {resp.text}")

            trigger_task = asyncio.create_task(trigger_appointment())
            
            # 5. Listen for WebSocket notification
            print("Waiting for notification via WebSocket...")
            message = await asyncio.wait_for(websocket.recv(), timeout=15)
            data = json.loads(message)
            print("\nRECEIVED WEBSOCKET MESSAGE:")
            print(json.dumps(data, indent=2))
            
            if data.get("type") == "notification" and data["data"]["type"] == "appointment_requested":
                print("\n✅ SUCCESS: Received appointment notification!")
                return True
            else:
                print("\n❌ FAILURE: Received unexpected message type.")
                return False
                
    except Exception as e:
        print(f"\n❌ CONNECTION ERROR: {e}")
        if hasattr(e, 'response'):
             print(f"Response: {e.response}")
        return False

if __name__ == "__main__":
    asyncio.run(verify_notifications())
