import asyncio
import httpx
import uuid
import sys
import os

# We're running INSIDE the docker network, so we use service names
BASE_URL = "http://backend:8000/api/v1"

async def check_backend_ready():
    async with httpx.AsyncClient() as client:
        for _ in range(30):
            try:
                resp = await client.get("http://backend:8000/health", timeout=2.0)
                if resp.status_code == 200:
                    print("Backend is READY")
                    return True
            except Exception:
                pass
            print("Waiting for backend...")
            await asyncio.sleep(2)
    return False

async def run_security_probes():
    print("\n=== STARTING DOCKER SECURITY PROBES ===\n")
    async with httpx.AsyncClient() as client:
        # 1. Setup
        doc_email = f"test_doc_{uuid.uuid4().hex[:4]}@saramedico.com"
        print(f"Registering Doctor: {doc_email}")
        reg_resp = await client.post(f"{BASE_URL}/auth/register", json={
            "email": doc_email,
            "password": "SecurePass123!",
            "full_name": "Dr. Docker Test",
            "role": "doctor",
            "organization_name": "Docker Test Hospital",
            "phone_number": "+16502530000"
        })
        # The backend returns a RedirectResponse (303) on success
        print(f"Doctor Registration Status: {reg_resp.status_code}")
        if reg_resp.status_code not in [201, 303]:
            print(f"Registration FAILED: {reg_resp.text}")
            return

        print("Logging in...")
        login_resp = await client.post(f"{BASE_URL}/auth/login", json={
            "email": doc_email,
            "password": "SecurePass123!"
        })
        
        if login_resp.status_code != 200:
            print(f"Login FAILED: {login_resp.status_code} - {login_resp.text}")
            return
            
        login_json = login_resp.json()
        if "access_token" not in login_json:
            print(f"Login response missing access_token: {login_json}")
            return
            
        doc_token = login_json["access_token"]
        headers = {"Authorization": f"Bearer {doc_token}"}

        # 2. RBAC Probes
        print("\n--- Testing RBAC ---")
        # Admin endpoint check
        admin_check = await client.get(f"{BASE_URL}/admin/overview", headers=headers)
        print(f"Doctor accessing Admin: {admin_check.status_code} (Expected 403)")

        # 3. Multi-Tenancy Probes
        print("\n--- Testing Multi-Tenancy ---")
        # Logic: Create a patient in Org A, try to access as Doctor from Org B
        p_onboard = await client.post(f"{BASE_URL}/patients", headers=headers, json={
            "email": f"pat_{uuid.uuid4().hex[:4]}@test.com",
            "password": "Pass123!",
            "full_name": "Patient Alpha",
            "phone_number": "+16502531111",
            "date_of_birth": "1990-01-01",
            "gender": "male"
        })
        patient_id = p_onboard.json()["id"]
        print(f"Patient Alpha Created: {patient_id}")

        # Register Doctor B
        doc_b_email = f"doc_b_{uuid.uuid4().hex[:4]}@test.com"
        await client.post(f"{BASE_URL}/auth/register", json={
            "email": doc_b_email,
            "password": "SecurePass123!",
            "full_name": "Dr. Beta",
            "role": "doctor",
            "organization_name": "Hospital Beta",
            "phone_number": "+16502532222"
        })
        login_b = await client.post(f"{BASE_URL}/auth/login", json={"email": doc_b_email, "password": "SecurePass123!"})
        headers_b = {"Authorization": f"Bearer {login_b.json()['access_token']}"}

        cross_access = await client.get(f"{BASE_URL}/patients/{patient_id}", headers=headers_b)
        print(f"Doctor B -> Patient A: {cross_access.status_code} (Expected 403 or 404)")

    print("\n=== DOCKER SECURITY PROBES COMPLETED ===\n")

if __name__ == "__main__":
    if not asyncio.run(check_backend_ready()):
        print("Backend failed to start in time. Exiting.")
        sys.exit(1)
    asyncio.run(run_security_probes())
