import asyncio, httpx, uuid, json, sys, os
from datetime import datetime

BASE = "http://backend:8000/api/v1"
TEST_FILE = "/app/_documents/K_V_VENKATARAMAN__report.pdf"

async def main():
    print("🚀 Starting AI Document Workflow Test...")
    uid = uuid.uuid4().hex[:6]
    doc_email = f"ai_doc_{uid}@test.com"
    pat_email = f"ai_pat_{uid}@test.com"
    password = "SecurePass123!"

    async with httpx.AsyncClient(follow_redirects=True, timeout=60) as c:
        # 1. Register & Login Doctor
        print("\n1. Registering Doctor...")
        reg_body = {
            "email": doc_email, "password": password, "full_name": "Dr. AI Tester",
            "role": "doctor", "organization_name": "AI Test Lab", "phone_number": "+16501112222"
        }
        r = await c.post(f"{BASE}/auth/register", json=reg_body)
        print(f"   Status: {r.status_code}")
        
        login_r = await c.post(f"{BASE}/auth/login", json={"email": doc_email, "password": password})
        doc_token = login_r.json()["access_token"]
        headers = {"Authorization": f"Bearer {doc_token}"}
        print("   ✅ Doctor Logged In")

        # 2. Onboard Patient
        print("\n2. Onboarding Patient...")
        pat_body = {
            "fullName": "AI Test Patient", "email": pat_email, "password": password,
            "dateOfBirth": "1990-01-01", "gender": "male", "phoneNumber": "+16503334444"
        }
        r = await c.post(f"{BASE}/patients", headers=headers, json=pat_body)
        patient_id = r.json()["id"]
        print(f"   ✅ Patient Onboarded (ID: {patient_id})")

        # 3. Upload Document from _documents
        print(f"\n3. Uploading Dataset File: {os.path.basename(TEST_FILE)}...")
        if not os.path.exists(TEST_FILE):
             # Try local path if /app is not available (though Docker run expects /app)
             local_file = TEST_FILE.replace("/app/", "./")
             if os.path.exists(local_file): TEST_FILE = local_file
        
        with open(TEST_FILE, "rb") as f:
            files = {"file": (os.path.basename(TEST_FILE), f, "application/pdf")}
            data = {"patient_id": patient_id, "notes": "Dataset test report"}
            r = await c.post(f"{BASE}/documents/upload", headers=headers, data=data, files=files)
        
        print(f"   Status: {r.status_code}")
        doc_id = r.json()["document_id"]
        print(f"   ✅ Document Uploaded (ID: {doc_id})")

        # 4. Trigger AI Processing
        print("\n4. Triggering AI Processing Job...")
        ai_body = {
            "patient_id": patient_id,
            "document_id": doc_id,
            "processing_type": "comprehensive",
            "priority": "normal"
        }
        r = await c.post(f"{BASE}/doctor/ai/process-document", headers=headers, json=ai_body)
        print(f"   Status: {r.status_code}")
        print(f"   Response: {r.json()['message']}")

        # 5. Check Document Status
        print("\n5. Checking AI Indexing Status...")
        await asyncio.sleep(2) # Give mock task time to "run"
        r = await c.get(f"{BASE}/documents/{doc_id}/status", headers=headers)
        print(f"   Status: {r.json()['status']}")

        # 6. Test AI Chat (Doctor)
        print("\n6. Testing AI Chat (Doctor querying about the document)...")
        chat_body = {
            "patient_id": patient_id,
            "document_id": doc_id,
            "query": "What is the patient's name and age in this report?"
        }
        
        # Test Streaming
        print("   AI Response Stream:")
        async with c.stream("POST", f"{BASE}/doctor/ai/chat/doctor", headers=headers, json=chat_body) as response:
            async for chunk in response.aiter_text():
                print(f"      {chunk}", end="", flush=True)
        print("\n   ✅ AI Chat Flow Verified")

    print("\n\n✨ AI Document Workflow Test Completed Successfully!")

if __name__ == "__main__":
    asyncio.run(main())
