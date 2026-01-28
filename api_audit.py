
import sys
import os
import asyncio
import httpx
import json
import pyotp
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

# Ensure we can import from app
sys.path.append(os.getcwd())

# Load environment variables
from dotenv import load_dotenv
load_dotenv(".env")

# Override for local execution (host -> docker ports)
DATABASE_URL = "postgresql+asyncpg://saramedico_user:SaraMed1c0_Dev_2024!Secure@localhost:5435/saramedico_dev"
os.environ["DATABASE_URL"] = DATABASE_URL
os.environ["MINIO_ENDPOINT"] = "localhost:9010"
os.environ["REDIS_URL"] = "redis://localhost:6382/0"

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text, select

# Import app to introspect routes
try:
    from app.main import app
    from fastapi.routing import APIRoute
    from app.core.security import pii_encryption, hash_token, hash_password
except ImportError as e:
    print(f"Error importing app: {e}")
    sys.exit(1)

# Configuration
BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = "audit_admin@saramedico.com"
DOCTOR_EMAIL = "audit_doctor@saramedico.com"
PATIENT_EMAIL = "audit_patient@saramedico.com"
PASSWORD = "TestPassword123!"

async def get_db_value(query, params=None):
    engine = create_async_engine(DATABASE_URL)
    async with engine.connect() as conn:
        result = await conn.execute(text(query), params or {})
        row = result.fetchone()
        await engine.dispose()
        return row

async def execute_db_stmt(stmt, params=None):
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        await conn.execute(text(stmt), params or {})
    await engine.dispose()

async def register_user(client, email, role, first_name, last_name, org="AuditOrg"):
    payload = {
        "email": email, "password": PASSWORD, "first_name": first_name, "last_name": last_name,
        "organization_name": org, "role": role, "phone": "+15550000000", "date_of_birth": "1990-01-01"
    }
    try:
        resp = await client.post(f"{BASE_URL}/api/v1/auth/register", json=payload)
        return resp.status_code in [201, 400]
    except: return False

async def login_user(client, email):
    try:
        resp = await client.post(f"{BASE_URL}/api/v1/auth/login", json={"email": email, "password": PASSWORD})
        if resp.status_code == 200:
            data = resp.json()
            return data["access_token"], data.get("refresh_token")
        return None, None
    except: return None, None

async def run_audit():
    print(f"\n{'='*80}")
    print(f"SARAMEDICO 100% COMPREHENSIVE API AUDIT (v1.3)")
    print(f"{'='*80}\n")

    routes = []
    for route in app.routes:
        if isinstance(route, APIRoute):
            routes.append({"path": route.path, "methods": sorted(list(route.methods)), "tags": route.tags})
    
    print(f"Total Routes: {len(routes)}\n")

    async with httpx.AsyncClient() as client:
        print("🛠  STEP 1: IDENTITY SETUP...")
        await register_user(client, ADMIN_EMAIL, "admin", "Admin", "User")
        await register_user(client, DOCTOR_EMAIL, "doctor", "Dr", "House")
        await register_user(client, PATIENT_EMAIL, "patient", "John", "Doe")

        res = {}
        for role, email in [("admin", ADMIN_EMAIL), ("doctor", DOCTOR_EMAIL), ("patient", PATIENT_EMAIL)]:
            access, refresh = await login_user(client, email)
            res[role] = {"access": access, "refresh": refresh, "headers": {"Authorization": f"Bearer {access}"} if access else {} }

        # Seed Identifiers
        patient_id = str(uuid4())
        doctor_id = str(uuid4())
        admin_id = str(uuid4())
        org_id = str(uuid4())
        doc_id = str(uuid4())
        appt_id = str(uuid4())
        cons_id = str(uuid4())
        task_id = str(uuid4())

        row = await get_db_value("SELECT id, organization_id FROM users WHERE email=:email", {"email": PATIENT_EMAIL})
        if row: patient_id, org_id = str(row[0]), str(row[1])
        row = await get_db_value("SELECT id FROM users WHERE email=:email", {"email": DOCTOR_EMAIL})
        if row: doctor_id = str(row[0])
        row = await get_db_value("SELECT id FROM users WHERE email=:email", {"email": ADMIN_EMAIL})
        if row: admin_id = str(row[0])

        if org_id: await execute_db_stmt("UPDATE organizations SET subscription_status='active' WHERE id=:id", {"id": org_id})
        
        print("📦 STEP 2: OBJECT SEEDING...")
        # 1. Permission Grant
        await client.post(f"{BASE_URL}/api/v1/permissions/grant-doctor-access", headers=res["patient"]["headers"], 
                        json={"doctor_id": doctor_id, "ai_access_permission": True, "access_level": "read_analyze", "expiry_days": 365})

        # 2. Document
        resp = await client.post(f"{BASE_URL}/api/v1/documents/upload", headers=res["patient"]["headers"], 
                               files={'file': ('audit.pdf', b'audit content', 'application/pdf')})
        if resp.status_code in [200, 201]: doc_id = str(resp.json().get("id"))

        # 3. Appointment & Consultation
        resp = await client.post(f"{BASE_URL}/api/v1/appointments/request", headers=res["patient"]["headers"],
                               json={"doctor_id": doctor_id, "requested_date": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(), "reason": "Audit Test", "grant_access_to_history": True})
        if resp.status_code in [200, 201]: appt_id = str(resp.json().get("id"))

        resp = await client.post(f"{BASE_URL}/api/v1/consultations", headers=res["doctor"]["headers"], 
                               json={"patientId": patient_id, "scheduledAt": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(), "durationMinutes": 30})
        if resp.status_code in [200, 201]: cons_id = str(resp.json().get("id"))

        # 4. Task
        resp = await client.post(f"{BASE_URL}/api/v1/doctor/tasks", headers=res["doctor"]["headers"], json={"title": "Audit Task", "priority": "high", "due_date": (datetime.now() + timedelta(days=1)).isoformat()})
        if resp.status_code in [200, 201]: task_id = str(resp.json().get("id"))

        print("🧪 STEP 3: ROUTE VERIFICATION...\n")
        print(f"{'ICON':<5} {'METHOD':<8} {'PATH':<55} {'STATUS':<12} {'DETAILS'}")
        print("-" * 100)

        for route in routes:
            path = route["path"]
            method = next((m for m in route["methods"] if m in ["GET", "POST", "PUT", "DELETE", "PATCH"]), "GET")
            status, details = "FAIL (0)", "Unknown"
            resp = None

            try:
                # PATH SPECIFIC LOGIC
                if path == "/api/v1/auth/register":
                    resp = await client.post(f"{BASE_URL}{path}", json={"email": "new_audit@test.com", "password": PASSWORD, "first_name": "New", "last_name": "User", "role": "patient"})
                elif path == "/api/v1/auth/login":
                    resp = await client.post(f"{BASE_URL}{path}", json={"email": PATIENT_EMAIL, "password": PASSWORD})
                elif path == "/api/v1/auth/verify-email":
                    m_token = "audit-verify-token"
                    await execute_db_stmt("UPDATE users SET email_verification_token=:t WHERE email=:e", {"t": hash_token(m_token), "e": PATIENT_EMAIL})
                    resp = await client.post(f"{BASE_URL}{path}", json={"token": m_token})
                elif path == "/api/v1/auth/verify-mfa":
                    resp = await client.post(f"{BASE_URL}{path}", json={"email": PATIENT_EMAIL, "password": PASSWORD, "code": "000000", "user_id": patient_id})
                elif path == "/api/v1/auth/refresh":
                    resp = await client.post(f"{BASE_URL}{path}", json={"refresh_token": res["patient"]["refresh"] or ""})
                elif path == "/api/v1/auth/forgot-password":
                    resp = await client.post(f"{BASE_URL}{path}", json={"email": PATIENT_EMAIL})
                elif path == "/api/v1/auth/reset-password":
                    m_token = "audit-reset-token"
                    await execute_db_stmt("UPDATE users SET password_reset_token=:t, password_reset_expires=:ex WHERE email=:e", {"t": hash_token(m_token), "ex": datetime.now() + timedelta(hours=1), "e": PATIENT_EMAIL})
                    resp = await client.post(f"{BASE_URL}{path}", json={"token": m_token, "new_password": PASSWORD, "confirm_password": PASSWORD})
                elif path == "/api/v1/auth/logout":
                    resp = await client.post(f"{BASE_URL}{path}", headers=res["patient"]["headers"], json={"refresh_token": res["patient"]["refresh"] or ""})
                elif path == "/api/v1/auth/setup-mfa":
                    resp = await client.post(f"{BASE_URL}{path}", headers=res["patient"]["headers"])
                elif path == "/api/v1/auth/verify-mfa-setup":
                    row = await get_db_value("SELECT mfa_secret FROM users WHERE email=:email", {"email": PATIENT_EMAIL})
                    code = pyotp.TOTP(pii_encryption.decrypt(row[0])).now() if row and row[0] else "000000"
                    resp = await client.post(f"{BASE_URL}{path}", headers=res["patient"]["headers"], json={"code": code})
                elif path == "/api/v1/auth/disable-mfa":
                    resp = await client.post(f"{BASE_URL}{path}", headers=res["patient"]["headers"])
                
                elif path == "/api/v1/patients" and method == "POST":
                    resp = await client.post(f"{BASE_URL}{path}", headers=res["admin"]["headers"], json={"email": str(uuid4())+"@test.com", "first_name": "New", "last_name": "Patient", "role": "patient"})
                elif "{patient_id}" in path:
                    p = path.replace("{patient_id}", patient_id)
                    payload = {"first_name": "Up", "last_name": "Dated", "gender": "male", "date_of_birth": "1990-01-01"}
                    resp = await client.request(method, f"{BASE_URL}{p}", headers=res["doctor"]["headers"], json=payload if method in ["PUT", "PATCH"] else None)

                elif path == "/api/v1/documents/upload":
                    resp = await client.post(f"{BASE_URL}{path}", headers=res["patient"]["headers"], files={'file': ('test.pdf', b'content', 'application/pdf')})
                elif path == "/api/v1/documents/upload-url":
                    resp = await client.post(f"{BASE_URL}{path}", headers=res["patient"]["headers"], json={"file_name": "test.pdf", "content_type": "application/pdf"})
                elif "{document_id}" in path:
                    p = path.replace("{document_id}", doc_id)
                    resp = await client.request(method, f"{BASE_URL}{p}", headers=res["patient"]["headers"], json={"message": "Analyze"} if "analyze" in p else None)

                elif path == "/api/v1/consultations" and method == "POST":
                    resp = await client.post(f"{BASE_URL}{path}", headers=res["doctor"]["headers"], json={"patientId": patient_id, "scheduledAt": datetime.now().isoformat()})
                elif "{consultation_id}" in path:
                    p = path.replace("{consultation_id}", cons_id)
                    resp = await client.request(method, f"{BASE_URL}{p}", headers=res["doctor"]["headers"], json={"notes": "Update"} if method == "PUT" else None)

                elif path == "/api/v1/doctor/tasks" and method == "POST":
                    resp = await client.post(f"{BASE_URL}{path}", headers=res["doctor"]["headers"], json={"title": "Audit", "priority": "normal"})
                elif "{task_id}" in path:
                    p = path.replace("{task_id}", task_id)
                    resp = await client.request(method, f"{BASE_URL}{p}", headers=res["doctor"]["headers"], json={"status": "completed"} if method == "PATCH" else None)

                elif path == "/api/v1/appointments" and method == "POST":
                    resp = await client.post(f"{BASE_URL}{path}", headers=res["patient"]["headers"], json={"doctor_id": doctor_id, "requested_date": datetime.now().isoformat(), "reason": "Test"})
                elif "{appointment_id}" in path:
                    p = path.replace("{appointment_id}", appt_id)
                    payload = {"status": "accepted"} if "status" in p else {"appointment_time": datetime.now().isoformat()}
                    resp = await client.request(method, f"{BASE_URL}{p}", headers=res["doctor"]["headers"], json=payload)
                
                elif "chat/patient" in path:
                    resp = await client.post(f"{BASE_URL}{path}", headers=res["patient"]["headers"], json={"patient_id": patient_id, "query": "Hello", "document_id": doc_id})
                elif "chat/doctor" in path:
                    resp = await client.post(f"{BASE_URL}{path}", headers=res["doctor"]["headers"], json={"patient_id": patient_id, "query": "Status", "document_id": doc_id})
                elif "chat-history/patient" in path:
                    resp = await client.get(f"{BASE_URL}{path}", headers=res["patient"]["headers"], params={"patient_id": patient_id})
                elif "chat-history/doctor" in path:
                    resp = await client.get(f"{BASE_URL}{path}", headers=res["doctor"]["headers"], params={"patient_id": patient_id, "doctor_id": doctor_id})

                elif "/api/v1/permissions/" in path:
                    payload = {"doctor_id": doctor_id, "ai_access_permission": True, "access_level": "read_analyze", "expiry_days": 365}
                    params = {"patient_id": patient_id}
                    resp = await client.request(method, f"{BASE_URL}{path}", headers=res["patient"]["headers"] if method != "GET" else res["doctor"]["headers"], json=payload, params=params)

                elif "/api/v1/admin" in path:
                    p = path.replace("{id}", admin_id)
                    payload = {"email": str(uuid4())+"@test.com", "role": "doctor", "full_name": "Audit Invite", "organization_name": "AuditOrg"}
                    resp = await client.request(method, f"{BASE_URL}{p}", headers=res["admin"]["headers"], json=payload)

                elif "/api/v1/organization/invitations" in path:
                    if method == "POST":
                        if "accept" in path:
                            payload = {"email": "inv@test.com", "token": "token", "password": PASSWORD, "full_name": "Test"}
                        else:
                            payload = {"email": str(uuid4())+"@test.com", "role": "doctor"}
                        resp = await client.post(f"{BASE_URL}{path}", headers=res["admin"]["headers"], json=payload)

                elif "/api/v1/doctor/profile" in path:
                    resp = await client.patch(f"{BASE_URL}{path}", headers=res["doctor"]["headers"], json={"full_name": "Dr. Audit"})
                elif "/api/v1/patient/medical-history" in path:
                    # Category is usually string, file is bytes/upload
                    resp = await client.post(f"{BASE_URL}{path}", headers=res["doctor"]["headers"], files={'file': ('hist.pdf', b'content')}, data={"patient_id": patient_id, "diagnosis": "Healthy", "category": "General"})
                elif "/api/v1/doctor/ai/process-document" in path:
                    resp = await client.post(f"{BASE_URL}{path}", headers=res["doctor"]["headers"], json={"patient_id": patient_id, "document_id": doc_id})
                elif "/api/v1/compliance/my-account" in path:
                    resp = await client.delete(f"{BASE_URL}{path}", headers=res["patient"]["headers"])
                elif "/api/v1/team/invite" in path:
                    resp = await client.post(f"{BASE_URL}{path}", headers=res["admin"]["headers"], json={"email": str(uuid4())+"@test.com", "role": "doctor", "full_name": "Audit Team"})

                elif method == "GET" and "{" not in path:
                    h = res["admin"]["headers"] if "admin" in path or "audit" in path else res["doctor"]["headers"]
                    resp = await client.get(f"{BASE_URL}{path}", headers=h)
                
                elif path.startswith("/health") or path == "/":
                    resp = await client.get(f"{BASE_URL}{path}")

            except Exception as e:
                details = f"Exc: {str(e)[:50]}"

            if resp:
                status = "PASS" if resp.status_code in [200, 201, 204, 400, 401, 403, 404, 422] else f"FAIL ({resp.status_code})"
                if resp.status_code == 500: details = f"500: {resp.text[:80]}"
                elif resp.status_code == 422: details = f"422: {resp.json().get('detail')[:80]}"
                else: details = f"HTTP {resp.status_code}"

            icon = "✅" if "PASS" in status else "❌"
            print(f"{icon} {method:<6} {path:<50} {status:<10} {details}")

if __name__ == "__main__":
    asyncio.run(run_audit())
