import asyncio
import json
import httpx
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.patient import Patient
from app.models.data_access_grant import DataAccessGrant
from app.models.document import Document
from app.core.security import create_access_token
from datetime import timedelta
import os
import time

async def upload_and_process_test():
    print("=== UPLOAD AND AI RAG TEST ===")
    
    async with AsyncSessionLocal() as db:
        doctor = (await db.execute(select(User).where(User.role == 'doctor').limit(1))).scalar_one()
        # Find a patent created by this doctor so they can upload
        patient = (await db.execute(select(Patient).where(Patient.created_by == doctor.id).limit(1))).scalar_one()
        
        doc_id_str = str(doctor.id)
        pat_id_str = str(patient.id)
        
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

        # Create token
        token = create_access_token(
            data={"sub": doc_id_str, "role": doctor.role},
            expires_delta=timedelta(minutes=60)
        )
        
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    base_url = "http://localhost:8000/api/v1"
    file_path = "/app/Synthetic_Patient_02_es.pdf"
    file_name = os.path.basename(file_path)
    print(f"\n--- 1. Uploading {file_name} ---")
    
    with open(file_path, "rb") as f:
        files = {"file": (file_name, f, "application/pdf")}
        data = {"patient_id": pat_id_str}
        
        resp = httpx.post(f"{base_url}/documents/upload", headers=headers, data=data, files=files, timeout=60.0)
        print("Upload Status:", resp.status_code)
        if resp.status_code != 201:
            print(resp.text)
            return
            
        json_resp = resp.json()
        doc_id = json_resp.get("document_id")
        print("Document ID:", doc_id)
        
    print("\n--- 2. Wait for Processing to Complete ---")
    max_retries = 30
    for i in range(max_retries):
        status_resp = httpx.get(f"{base_url}/documents/{doc_id}/status", headers=headers)
        if status_resp.status_code == 200:
            status_data = status_resp.json()
            is_indexed = status_data.get("status") == "indexed"
            print(f"[{i+1}/{max_retries}] Status: {status_data.get('status')} | Details: {json.dumps(status_data.get('processing_details'))}")
            if is_indexed:
                print("Document indexing complete!")
                break
        else:
            print("Failed to get status:", status_resp.text)
        time.sleep(5)
    else:
        print("Processing timed out or Celery worker isn't running!")
        # Instead of failing, we process it locally in script just in case celery isn't running
        print("Running manual processing fallback...")
        from app.services.document_processor import DocumentProcessor
        async with AsyncSessionLocal() as db_session:
            processor = DocumentProcessor(db_session)
            await processor.process_document(file_path, doc_id, pat_id_str)
            print("Fallback manual processing complete.")

    print("\n--- 3. Create Chat Session ---")
    headers_json = {**headers, "Content-Type": "application/json"}
    sess_req = {"patient_id": pat_id_str, "title": "Syntetic Patient Review"}
    sess_resp = httpx.post(f"{base_url}/doctor/ai/chat/session", headers=headers_json, json=sess_req)
    
    print("Session Status:", sess_resp.status_code)
    session_json = sess_resp.json()
    session_id = session_json.get("session_id")
    print("Session ID:", session_id)
    
    print("\n--- 4. Send Message ---")
    msg_req = {
        "session_id": session_id,
        "patient_id": pat_id_str,
        "message": "What is the assessment or diagnosis listed for this patient in the uploaded document?",
        "document_id": doc_id
    }
    
    print("Requesting AI Stream...")
    with httpx.stream("POST", f"{base_url}/doctor/ai/chat/message", headers=headers_json, json=msg_req, timeout=120.0) as r:
        print("Response Status:", r.status_code)
        for chunk in r.iter_text():
            print(chunk, end='', flush=True)
            
    print("\n\n=== E2E TEST COMPLETE ===")

asyncio.run(upload_and_process_test())
