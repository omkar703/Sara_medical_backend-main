import asyncio
import uuid
import json
import httpx
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.patient import Patient
from app.models.data_access_grant import DataAccessGrant
from app.core.security import create_access_token
from datetime import timedelta

async def test_apis():
    async with AsyncSessionLocal() as db:
        doctor = (await db.execute(select(User).where(User.role == 'doctor').limit(1))).scalar_one()
        patient = (await db.execute(select(Patient).limit(1))).scalar_one()
        
        # Ensure AI access
        existing = (await db.execute(
            select(DataAccessGrant).where(
                DataAccessGrant.doctor_id == doctor.id,
                DataAccessGrant.patient_id == patient.id,
                DataAccessGrant.ai_access_permission == True
            )
        )).scalar_one_or_none()
        if not existing:
            db.add(DataAccessGrant(doctor_id=doctor.id, patient_id=patient.id, status='active', is_active=True, ai_access_permission=True))
            await db.commit()
            
        doc_id_str = str(doctor.id)
        pat_id_str = str(patient.id)
        
        # Create token
        token = create_access_token(
            data={"sub": doc_id_str, "role": doctor.role},
            expires_delta=timedelta(minutes=60)
        )
        
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    base_url = "http://localhost:8000/api/v1"
    
    print("--- 1. POST /doctor/ai/chat/session ---")
    req1 = {"patient_id": pat_id_str, "title": "Checkup Review"}
    print("REQ_JSON:", json.dumps(req1))
    resp1 = httpx.post(f"{base_url}/doctor/ai/chat/session", headers=headers, json=req1)
    print("RESP_STATUS:", resp1.status_code)
    try:
        resp1_json = resp1.json()
        print("RESP_JSON:", json.dumps(resp1_json))
        session_id = resp1_json.get("session_id")
    except Exception as e:
        print("Error parsing response:", resp1.text)
        return

    print("\n--- 2. POST /doctor/ai/chat/message ---")
    req2 = {
        "session_id": session_id,
        "patient_id": pat_id_str,
        "message": "Please summarize the latest lab results.",
        "document_id": None
    }
    print("REQ_JSON:", json.dumps(req2))
    # Using streaming request
    with httpx.stream("POST", f"{base_url}/doctor/ai/chat/message", headers=headers, json=req2, timeout=60.0) as r:
        print("RESP_STATUS:", r.status_code)
        streamed_text = ""
        for chunk in r.iter_text():
            streamed_text += chunk
        print("RESP_TEXT (Stream):", streamed_text)

    print("\n--- 3. GET /doctor/ai/chat/sessions ---")
    resp3 = httpx.get(f"{base_url}/doctor/ai/chat/sessions?patient_id={pat_id_str}", headers=headers)
    print("RESP_STATUS:", resp3.status_code)
    try:
        print("RESP_JSON:", json.dumps(resp3.json()))
    except:
        pass

    print(f"\n--- 4. GET /doctor/ai/chat/session/{session_id} ---")
    resp4 = httpx.get(f"{base_url}/doctor/ai/chat/session/{session_id}", headers=headers)
    print("RESP_STATUS:", resp4.status_code)
    try:
        print("RESP_JSON:", json.dumps(resp4.json()))
    except:
        pass

asyncio.run(test_apis())
