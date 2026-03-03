import requests
import json
import uuid
import os
import time

BASE_URL = "http://localhost:8000/api/v1"
ENV_FILE = "ai_test_prerequisites.env"

# In-memory store before saving to .env
TEST_STATE = {
    "DOCTOR_EMAIL": f"test_doc_ai_{str(uuid.uuid4())[:6]}@example.com",
    "DOCTOR_PASS": "SecureDocPass123!",
    "PATIENT_EMAIL": f"test_pat_ai_{str(uuid.uuid4())[:6]}@example.com",
    "PATIENT_PASS": "SecurePatPass123!",
    "DOCTOR_ID": None,
    "DOCTOR_TOKEN": None,
    "PATIENT_USER_ID": None,
    "PATIENT_TOKEN": None,
    "PATIENT_PROFILE_ID": None,
    "DOCUMENT_ID": None,
    "JOB_ID": None
}

def print_step(title):
    print(f"\n{'='*60}")
    print(f" ⚙️  {title}")
    print(f"{'='*60}")

def print_result(response):
    if response.ok:
        print(f"✅ Status: {response.status_code}")
    else:
        print(f"❌ Status: {response.status_code} - {response.text}")
    return response

def save_env():
    print(f"\n💾 Saving prerequisites to {ENV_FILE}...")
    with open(ENV_FILE, "w") as f:
        for key, value in TEST_STATE.items():
            if value:
                f.write(f"{key}={value}\n")
    print(f"✅ Saved! You can load these values for future testing.")

# ==========================================
# Phase 1: Authentication & Setup
# ==========================================

def setup_users():
    print_step("PHASE 1: Setting up Users & Authentication")
    
    # 1. Register Doctor
    print("\n--- Registering Doctor ---")
    reg_resp = requests.post(f"{BASE_URL}/auth/register", json={
        "email": TEST_STATE["DOCTOR_EMAIL"], "password": TEST_STATE["DOCTOR_PASS"],
        "confirm_password": TEST_STATE["DOCTOR_PASS"], "role": "doctor"
    })
    print_result(reg_resp)
    
    # 2. Register Patient User (Wait, Patients can't register themselves via auth/register typically... 
    # Let's check if the generic auth/register works. If it returns 403, we use Doctor to onboard
    # But earlier test showed 403 for patient registration. 
    # Usually patients are invited or created by admins. Let's try Doctor onboarding flow.
    print("\n--- Logging in Doctor ---")
    doc_login = requests.post(f"{BASE_URL}/auth/login", json={
        "email": TEST_STATE["DOCTOR_EMAIL"], "password": TEST_STATE["DOCTOR_PASS"]
    })
    if doc_login.ok:
        TEST_STATE["DOCTOR_TOKEN"] = doc_login.json()["access_token"]
        TEST_STATE["DOCTOR_ID"] = doc_login.json()["user"]["id"]
    else:
        print("❌ Doctor login failed", doc_login.text)
        return False
        
    print("\n--- Creating Patient Profile via Doctor ---")
    # Using the /patients endpoint to onboard a patient
    pat_req = requests.post(f"{BASE_URL}/patients", 
        headers={"Authorization": f"Bearer {TEST_STATE['DOCTOR_TOKEN']}"},
        json={
            "fullName": "AI Test Patient",
            "dateOfBirth": "1980-05-15",
            "gender": "other",
            "phoneNumber": "+12025550147",
            "email": TEST_STATE["PATIENT_EMAIL"],
            "password": TEST_STATE["PATIENT_PASS"]
        }
    )
    if pat_req.ok:
        TEST_STATE["PATIENT_PROFILE_ID"] = pat_req.json()["id"]
        # The system likely sends an invite email or creates the user.
        # But to test the backend, we might need a raw user for the patient token if they need to chat.
        # Often /patients just creates a profile. Let's force create a patient user if we can.
    else:
        print("❌ Patient creation failed", pat_req.text)
        return False
        
    # Hack for test: if patient login via auth/login doesn't work out of the box after onboard, 
    # we might need to simulate password reset or just use the doctor token for tests that allow it.
    # Let's assume the backend automatically assigns a default pass or we might just skip the pure patient token 
    # tests if not possible to script easily, but let's try to just do the doctor ones first.
    return True

# ==========================================
# Phase 2: Generating Data (Documents & Grants)
# ==========================================

def setup_data():
    print_step("PHASE 2: Generating Documents and Grants")
    
    import glob
    import random
    
    # 3. Upload Document from host folder
    print("\n--- Uploading Document for AI Processing ---")
    
    records_dir = "/app/medical-records"
    # Find all files except directories
    available_files = [f for f in glob.glob(f"{records_dir}/*") if os.path.isfile(f)]
    
    if not available_files:
        print("❌ No files found in medical-records folder to upload.")
        return
        
    random_doc_path = random.choice(available_files)
    file_name = os.path.basename(random_doc_path)
    
    # Map extension to content type
    ext = file_name.lower().split('.')[-1]
    content_map = {'pdf': 'application/pdf', 'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg'}
    content_type = content_map.get(ext, 'application/octet-stream')

    with open(random_doc_path, "rb") as f:
        doc_req = requests.post(f"{BASE_URL}/documents/upload",
            headers={"Authorization": f"Bearer {TEST_STATE['DOCTOR_TOKEN']}"},
            data={"patient_id": TEST_STATE["PATIENT_PROFILE_ID"]},
            files={"file": (file_name, f, content_type)}
        )
        
    if doc_req.ok:
        TEST_STATE["DOCUMENT_ID"] = doc_req.json().get("document_id") or doc_req.json().get("id")
        print(f"✅ Document uploaded: {TEST_STATE['DOCUMENT_ID']}")
    else:
        print("❌ Upload failed:", upload_resp.text)
        
    # Clean up dummy file


    # 2. Wait for processing (In a real system Celery does this)
    # The document needs to be "confirmed" or processed. We'll proceed immediately.
    
    # 3. Create Data Access Grant
    print("\n--- Granting AI Access Permissions ---")
    # First, login as Patient to get the patient token
    # The /patients endpoint onboarded them, but usually they need to be registered in auth.
    # Let's register a user for the patient so they can login.
    print("Setting up patient auth account...")
    requests.post(f"{BASE_URL}/auth/register", json={
        "email": TEST_STATE["PATIENT_EMAIL"], "password": TEST_STATE["PATIENT_PASS"],
        "confirm_password": TEST_STATE["PATIENT_PASS"], "role": "patient",
        "date_of_birth": "1980-05-15"
    })
    
    pat_login = requests.post(f"{BASE_URL}/auth/login", json={
        "email": TEST_STATE["PATIENT_EMAIL"], "password": TEST_STATE["PATIENT_PASS"]
    })
    
    if pat_login.ok:
        TEST_STATE["PATIENT_TOKEN"] = pat_login.json()["access_token"]
        # Grant doctor access using patient token
        grant_req = requests.post(
            f"{BASE_URL}/permissions/grant-doctor-access", 
            headers={"Authorization": f"Bearer {TEST_STATE['PATIENT_TOKEN']}"}, 
            json={
                "doctor_id": TEST_STATE["DOCTOR_ID"],
                "ai_access_permission": True,
                "access_level": "read_analyze"
            }
        )
        print_result(grant_req)
    else:
        print("❌ Patient login failed, cannot grant access.")

# ==========================================
# Phase 3: AI endpoints Execution
# ==========================================

def execute_ai_tests():
    print_step("PHASE 3: Testing AI Endpoints")
    headers = {"Authorization": f"Bearer {TEST_STATE['DOCTOR_TOKEN']}"}
    
    # 1. Process Document
    print("\n--- POST /doctor/ai/process-document ---")
    proc_resp = requests.post(f"{BASE_URL}/doctor/ai/process-document", headers=headers, json={
        "patient_id": TEST_STATE["PATIENT_PROFILE_ID"],
        "document_id": TEST_STATE["DOCUMENT_ID"],
        "processing_type": "text_only",
        "priority": "normal"
    })
    
    data = print_result(proc_resp)
    if proc_resp.ok:
        TEST_STATE["JOB_ID"] = proc_resp.json().get("job_id")
        print(f"Job ID mapped to: {TEST_STATE['JOB_ID']}")
        
        # Poll for status
        import time
        max_attempts = 5
        print("\n--- Checking AI Processing Status ---")
        for i in range(max_attempts):
            status_req = requests.get(
                f"{BASE_URL}/doctor/ai/process-document/{TEST_STATE['JOB_ID']}",
                headers=headers
            )
            if status_req.ok:
                doc_status = status_req.json()
                print(f"Status check {i+1}: {doc_status}")
                if doc_status['status'] == "completed":
                    print("✅ Document AI processing is fully complete!")
                    break
                elif doc_status['status'] == "failed":
                    print(f"❌ Document processing failed: {doc_status.get('message')}")
                    break
            else:
                print(f"❌ Status check failed: {status_req.status_code} - {status_req.text}")
                break
            time.sleep(1)

    # 2. Chat Doctor
    print("\n--- POST /doctor/ai/chat/doctor ---")
    chat_resp = requests.post(f"{BASE_URL}/doctor/ai/chat/doctor", headers=headers, stream=True, json={
        "patient_id": TEST_STATE["PATIENT_PROFILE_ID"],
        "document_id": TEST_STATE["DOCUMENT_ID"],
        "query": "What are the key points in this document?"
    })
    print(f"Status Code: {chat_resp.status_code}")
    if chat_resp.ok:
        print("Stream Content Received (First 100 chars): ", chat_resp.text)
        stream_content = ""
        try:
            for chunk in chat_resp.iter_content(chunk_size=1024):
                if chunk:
                    stream_content += chunk.decode('utf-8')
                    if len(stream_content) > 100: break
            # print(stream_content[:100] + "...")
        except Exception as e:
            print("Stream reading error:", e)
    else:
        print("Response:", chat_resp.text)

    # 3. Doctor Chat History
    print("\n---   GET /doctor/ai/chat-history/doctor ---")
    hist_resp = requests.get(
        f"{BASE_URL}/doctor/ai/chat-history/doctor?patient_id={TEST_STATE['PATIENT_PROFILE_ID']}",
        headers=headers
    )
    print_result(hist_resp)
    if hist_resp.ok:
        records = hist_resp.json().get("history", [])
        print(f"Retrieved {len(records)} history records.")

    # 4. Patient Chat — patient asks about their own document
    print("\n--- POST /patient/ai/chat/patient ---")
    pat_headers = {"Authorization": f"Bearer {TEST_STATE['PATIENT_TOKEN']}"}
    
    # Decode patient_id from the JWT token (sub field)
    from jose import jwt as jose_jwt
    patient_jwt_payload = jose_jwt.get_unverified_claims(TEST_STATE["PATIENT_TOKEN"])
    patient_user_id = patient_jwt_payload.get("sub")
    
    patient_chat_resp = requests.post(
        f"{BASE_URL}/doctor/ai/chat/patient",
        headers=pat_headers,
        stream=True,
        json={
            "patient_id":  patient_user_id,
            "document_id": TEST_STATE["DOCUMENT_ID"],
            "query": "Can you summarize my medical report?"
        }
    )
    print(f"Status Code: {patient_chat_resp.status_code}")
    if patient_chat_resp.ok:
        stream_content = ""
        for chunk in patient_chat_resp.iter_content(chunk_size=1024):
            if chunk:
                stream_content += chunk.decode("utf-8")
                if len(stream_content) > 200:
                    break
        print(f"✅ Patient Chat Response (first 200 chars):\n{stream_content[:200]}...")
    else:
        print(f"❌ Failed: {patient_chat_resp.text}")

    # 5. Patient Chat History
    print("\n--- GET /patient/ai/chat-history/patient ---")
    hist_pat_resp = requests.get(
        f"{BASE_URL}/doctor/ai/chat-history/patient?patient_id={patient_user_id}",
        headers=pat_headers
    )
    print_result(hist_pat_resp)
    if hist_pat_resp.ok:
        records = hist_pat_resp.json().get("history", [])
        print(f"✅ Retrieved {len(records)} patient history records.")


def run():
    print("🚀 Starting AI Integrations Pre-requisite Setup & Test Engine...\n")
    if setup_users():
        setup_data()
        save_env()  # ✅ Save to .env BEFORE running AI to ensure we have the IDs saved
        execute_ai_tests()
    else:
        print("❌ Setup failed. Cannot proceed to AI testing.")

if __name__ == "__main__":
    try:
        run()
    except requests.exceptions.ConnectionError:
        print("\n❌ CONNECTION ERROR: Could not connect to the backend server.")
        print("Please ensure the backend API is running at http://localhost:8000")
    except Exception as e:
        import traceback
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        traceback.print_exc()
