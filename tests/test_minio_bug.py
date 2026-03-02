import asyncio
import httpx
import uuid
import sys

async def test_minio_presigned():
    print("🚀 Testing MinIO Presigned URL generation...")
    # We need to be logged in to hit doctor/patients/{id}/documents
    # or just use a dummy endpoint that calls minio_service.generate_presigned_url
    
    # Actually, I can just try to run a script inside the container that calls MinIOService directly.
    # But since I'm testing the API, let's do an API call.
    
    BASE = "http://localhost:8000/api/v1"
    
    async with httpx.AsyncClient(timeout=30) as client:
        # 1. Login
        print("Logging in...")
        try:
            # Reusing credentials from previous tests
            login_data = {"email": "doctor@hospital.com", "password": "SecurePass123!"}
            r = await client.post(f"{BASE}/auth/login", json=login_data)
            if r.status_code != 200:
                print(f"Login failed: {r.status_code} {r.text}")
                return
            token = r.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # 2. Get Patients to find an ID
            r = await client.get(f"{BASE}/patients", headers=headers)
            patients = r.json().get("patients", [])
            if not patients:
                print("No patients found. Attempting to create one...")
                pat_body = {
                    "fullName": "MinIO Test Patient", "email": f"minio_pat_{uuid.uuid4().hex[:6]}@test.com", 
                    "password": "SecurePass123!", "dateOfBirth": "1990-01-01", "gender": "male", 
                    "phoneNumber": "+16501112233"
                }
                r = await client.post(f"{BASE}/patients", headers=headers, json=pat_body)
                patient_id = r.json()["id"]
            else:
                patient_id = patients[0]["id"]
            
            print(f"Using patient_id: {patient_id}")
            
            # 3. Request documents (this should trigger minio presigned url generation)
            print("Requesting patient documents (presigned URL generation)...")
            r = await client.get(f"{BASE}/doctor/patients/{patient_id}/documents", headers=headers)
            print(f"Status: {r.status_code}")
            print(f"Body: {r.text}")
            
        except Exception as e:
            print(f"Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_minio_presigned())
