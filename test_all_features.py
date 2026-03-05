import asyncio
import json
import uuid
from datetime import datetime, timedelta
from sqlalchemy import select, delete
from httpx import AsyncClient
from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.patient import Patient
from app.models.notification import Notification
from app.core.security import create_access_token
from app.models.appointment import Appointment
from app.models.task import Task
from app.models.data_access_grant import DataAccessGrant

# Configuration
BASE_URL = "http://localhost:8000/api/v1"

async def get_test_users():
    async with AsyncSessionLocal() as db:
        doctor = (await db.execute(select(User).where(User.role == 'doctor'))).scalars().first()
        admin = (await db.execute(select(User).where(User.role == 'admin'))).scalars().first()
        hospital = (await db.execute(select(User).where(User.role == 'hospital'))).scalars().first()
        res = await db.execute(select(Patient))
        patients = res.scalars().all()
        target_patient_model = None
        target_patient_user = None
        for p in patients:
            u = (await db.execute(select(User).where(User.id == p.id))).scalars().first()
            if u:
                target_patient_model = p
                target_patient_user = u
                break
        return doctor, target_patient_user, target_patient_model, admin, hospital

async def create_tokens(doctor, patient_user, admin, hospital):
    def make_token(user):
        return create_access_token(data={"sub": str(user.id), "role": user.role}, expires_delta=timedelta(hours=1)) if user else None
    return {"doctor": make_token(doctor), "patient": make_token(patient_user), "admin": make_token(admin), "hospital": make_token(hospital)}

async def run_tests():
    print("--- 🚀 STARTING COMPREHENSIVE TESTS ---")
    doctor, patient_user, patient_model, admin, hospital = await get_test_users()
    if not (doctor and patient_user and admin and hospital):
        print("❌ Missing required users.")
        return
    tokens = await create_tokens(doctor, patient_user, admin, hospital)
    
    async with AsyncSessionLocal() as db:
        await db.execute(delete(DataAccessGrant).where(DataAccessGrant.patient_id == patient_user.id, DataAccessGrant.doctor_id == doctor.id))
        await db.execute(delete(Notification).where(Notification.user_id.in_([doctor.id, patient_user.id, hospital.id])))
        await db.commit()
    
    async with AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
        # 1. Credential Extraction
        print("\n--- 🧠 AI: Credential Extraction ---")
        try:
             with open("/app/MBBS-DEGREE-rotated-1.jpg", "rb") as f:
                resp = await client.post("/doctor/extract-credentials", headers={"Authorization": f"Bearer {tokens['doctor']}"}, files={"certificate_image": ("MBBS_Certificate.jpg", f, "image/jpeg")})
                if resp.status_code == 200: print("✅ Success")
                else: print(f"❌ Failed: {resp.status_code}")
        except: print("⚠️ Image not found.")

        # 2. Permission (Grant first, then test chat)
        print("\n--- 🤝 Permission & AI Chat ---")
        perm_data = {"doctor_id": str(doctor.id), "ai_access_permission": True, "reason": "Test Grant"}
        resp = await client.post("/permissions/grant-doctor-access", headers={"Authorization": f"Bearer {tokens['patient']}"}, json=perm_data)
        if resp.status_code == 201:
            print("✅ Permission Granted")
            # Now test chat
            req_data = {"patient_id": str(patient_model.id), "title": "Test Session"}
            resp = await client.post("/doctor/ai/chat/session", headers={"Authorization": f"Bearer {tokens['doctor']}"}, json=req_data)
            if resp.status_code in [200, 201]: print(f"✅ AI Session Created: {resp.json().get('session_id')}")
            else: print(f"❌ AI Session Failed: {resp.status_code} - {resp.text}")
        else: print(f"❌ Permission Grant Failed: {resp.status_code}")

        # 3. Notification Triggers
        print("\n--- 🔔 Notifications ---")
        
        # 3.1 Appointment
        print("Testing: Appointment flow")
        app_data = {"doctor_id": str(doctor.id), "requested_date": (datetime.utcnow() + timedelta(days=2)).isoformat(), "reason": "Test", "grant_access_to_history": False}
        resp = await client.post("/appointments", headers={"Authorization": f"Bearer {tokens['patient']}"}, json=app_data)
        if resp.status_code == 201:
            appt_id = resp.json().get("id")
            print("✅ Appointment Requested")
            # Approve
            approve_data = {"appointment_time": (datetime.utcnow() + timedelta(days=2)).isoformat()}
            resp = await client.post(f"/appointments/{appt_id}/approve", headers={"Authorization": f"Bearer {tokens['doctor']}"}, json=approve_data)
            if resp.status_code == 200:
                print("✅ Appointment Approved")
                await asyncio.sleep(1)
                async with AsyncSessionLocal() as db:
                    n1 = (await db.execute(select(Notification).where(Notification.user_id == doctor.id, Notification.type == "appointment_requested"))).scalars().first()
                    n2 = (await db.execute(select(Notification).where(Notification.user_id == patient_user.id, Notification.type == "appointment_approved"))).scalars().first()
                    if n1: print(f"✅ Doctor notified of request")
                    if n2: print(f"✅ Patient notified of approval")
            else: print(f"❌ Approval Failed: {resp.status_code} - {resp.text}")

        # 3.2 Urgent Task
        print("Testing: Urgent Task")
        task_data = {"title": "URGENT TEST", "priority": "urgent", "status": "pending", "due_date": (datetime.utcnow() + timedelta(hours=2)).isoformat(), "doctor_id": str(doctor.id), "assigned_to": str(doctor.id)}
        resp = await client.post("/doctor/tasks", headers={"Authorization": f"Bearer {tokens['doctor']}"}, json=task_data)
        if resp.status_code == 201:
            print("✅ Urgent Task Created")
            await asyncio.sleep(1)
            async with AsyncSessionLocal() as db:
                n = (await db.execute(select(Notification).where(Notification.user_id == hospital.id, Notification.type == "urgent_task"))).scalars().first()
                if n: print(f"✅ Hospital Admin notified of urgent task")

    print("\n--- ✅ COMPREHENSIVE TESTS COMPLETED ---")

if __name__ == "__main__": asyncio.run(run_tests())
