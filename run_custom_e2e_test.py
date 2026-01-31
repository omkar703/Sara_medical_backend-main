
import httpx
import io
import os
import sys
import json
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
from uuid import UUID
from sqlalchemy import select

# Setup environment like the original script
sys.path.append(os.path.join(os.getcwd(), "backend"))
load_dotenv("backend/.env")

# Patch DATABASE_URL for local execution (only if not in docker)
# if os.environ.get("DATABASE_URL") and not os.path.exists("/.dockerenv"):
#    os.environ["DATABASE_URL"] = os.environ["DATABASE_URL"].replace("@postgres:", "@localhost:")

# Imports from app must happen after sys.path setup
# from app.database import AsyncSessionLocal
# from app.models.patient import Patient

BASE_URL = "http://localhost:8000/api/v1"

# Folder containing user documents
DOCUMENTS_DIR = os.path.join(os.getcwd(), "_documents")

# Global test data storage for the report
test_data = {
    "users": [],
    "documents": [],
    "appointments": [],
    "tasks": [],
    "zoom_meetings": [],
    "endpoint_calls": []  # To store raw request/response for the report
}

def log_api_call(method, endpoint, payload, response_status, response_data):
    """Helper to log API usage for the report"""
    test_data["endpoint_calls"].append({
        "timestamp": datetime.now().isoformat(),
        "method": method,
        "endpoint": endpoint,
        "payload": payload if isinstance(payload, (dict, list)) else "BINARY_OR_FORM_DATA",
        "status": response_status,
        "response": response_data
    })

def print_section(title):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")  

def run_custom_e2e_test():
    print_section("STARTING CUSTOM E2E TEST: 4 PATIENTS, 5 DOCTORS, REAL DATA")
    
    timestamp = int(datetime.utcnow().timestamp())
    
    # 1. Define Users
    users_config = []
    
    # 5 Patients
    for i in range(1, 6):
        users_config.append({
            "email": f"custom_patient{i}_{timestamp}@test.com",
            "password": "SecurePass123!",
            "full_name": f"Patient {i} Test",
            "role": "patient",
            "type": f"patient{i}",
            "date_of_birth": "1980-01-01",
            "phone_number": "+1555000000" + str(i)
        })
        
    # 5 Doctors
    specialties = ["Cardiology", "Dermatology", "Pediatrics", "Neurology", "Orthopedics"]
    for i in range(1, 6):
        users_config.append({
            "email": f"custom_doctor{i}_{timestamp}@test.com",
            "password": "SecurePass123!",
            "full_name": f"Dr. {i} Test",
            "role": "doctor",
            "specialty": specialties[i-1],
            "license": f"LIC-{i}-{timestamp}",
            "type": f"doctor{i}",
            "date_of_birth": "1975-01-01",
            "phone_number": "+1555111000" + str(i)
        })

    registered_users = {}
    doctor_tokens = []
    
    # Store docs for AI step later
    patient_docs = {}
    patients_to_create_db_profile = []

    # 2. Register & Login Users
    print_section("STEP 1: Registering and Logging in Users")
    # 2. Register & Login Healthcare Providers First
    print_section("STEP 1: Registering Healthcare Providers & Onboarding Patients")
    
    # 2a. Register Doctors
    for user in [u for u in users_config if u["role"] != "patient"]:
        reg_payload = {
            "email": user["email"],
            "password": user["password"],
            "full_name": user["full_name"],
            "role": user["role"],
            "date_of_birth": user.get("date_of_birth"),
            "phone_number": user.get("phone_number"),
            "organization_name": "Test Hospital"
        }
        if user["role"] == "doctor":
            reg_payload["specialty"] = user["specialty"]
            reg_payload["license_number"] = user["license"]

        print(f"Registering Provider {user['full_name']}...")
        try:
            resp = httpx.post(f"{BASE_URL}/auth/register", json=reg_payload, timeout=30.0)
            log_api_call("POST", "/auth/register", reg_payload, resp.status_code, resp.json() if resp.status_code < 500 else resp.text)
            
            if resp.status_code != 201:
                print(f"  ✗ Provider Registration Failed: {resp.text}")
                continue
                
            user_id = resp.json()["id"]
            
            # Login
            login_payload = {"email": user["email"], "password": user["password"]}
            resp = httpx.post(f"{BASE_URL}/auth/login", json=login_payload, timeout=10.0)
            log_api_call("POST", "/auth/login", login_payload, resp.status_code, "HIDDEN_TOKEN_RESPONSE")

            if resp.status_code == 200:
                print(f"  ✓ Success: {user['full_name']}")
                login_data = resp.json()
                token = login_data["access_token"]
                
                registered_users[user["email"]] = {
                    "id": user_id,
                    "token": token,
                    "role": user["role"],
                    "name": user["full_name"],
                    "email": user["email"]
                }
                registered_users[user["type"]] = registered_users[user["email"]]
                test_data["users"].append({"email": user["email"], "id": user_id, "role": user["role"], "type": user["type"]})
                if user["role"] == "doctor":
                    doctor_tokens.append(token)

            else:
                print(f"  ✗ Login Failed: {resp.text}")

        except Exception as e:
            print(f"  ✗ Exception: {str(e)}")

    # 2b. Doctors Onboard Patients
    for i, user in enumerate([u for u in users_config if u["role"] == "patient"]):
        # Vary the doctor: P1 by D1, P2 by D2, etc.
        doctor_idx = (i % len(doctor_tokens)) + 1
        doctor_key = f"doctor{doctor_idx}"
        doctor_token = registered_users[doctor_key]["token"]
        
        onboard_payload = {
            "fullName": user["full_name"],
            "dateOfBirth": user["date_of_birth"],
            "phoneNumber": user["phone_number"],
            "email": user["email"],
            "password": user["password"],
            "gender": "male"
        }

        print(f"Onboarding Patient {user['full_name']} via {registered_users[doctor_key]['name']}...")
        try:
            headers = {"Authorization": f"Bearer {doctor_token}"}
            resp = httpx.post(f"{BASE_URL}/patients", json=onboard_payload, headers=headers, timeout=30.0)
            log_api_call("POST", "/patients", onboard_payload, resp.status_code, resp.json() if resp.status_code < 500 else resp.text)
            
            if resp.status_code != 201:
                print(f"  ✗ Onboarding Failed: {resp.text}")
                continue
            
            patient_response = resp.json()
            patient_id = patient_response["id"]
            
            # Now Login as Patient
            login_payload = {"email": user["email"], "password": user["password"]}
            resp = httpx.post(f"{BASE_URL}/auth/login", json=login_payload, timeout=10.0)
            log_api_call("POST", "/auth/login", login_payload, resp.status_code, "HIDDEN_TOKEN_RESPONSE")

            if resp.status_code == 200:
                print(f"  ✓ Patient Logged In: {user['full_name']}")
                login_data = resp.json()
                token = login_data["access_token"]
                
                registered_users[user["email"]] = {
                    "id": patient_id,
                    "token": token,
                    "role": "patient",
                    "name": user["full_name"],
                    "email": user["email"],
                    "onboarded_by": registered_users[doctor_key]['id']
                }
                registered_users[user["type"]] = registered_users[user["email"]]
                test_data["users"].append({"email": user["email"], "id": patient_id, "role": "patient", "type": user["type"]})
        except Exception as e:
            print(f"  ✗ Exception: {str(e)}")

    # 2c. Verify that patients can't self-register
    print("\nVerifying Self-Registration Restriction...")
    fail_payload = {
        "email": f"fail_patient_{timestamp}@test.com",
        "password": "SecurePass123!",
        "full_name": "Should Fail",
        "role": "patient",
        "date_of_birth": "1980-01-01",
        "organization_name": "Test Hospital"
    }
    resp = httpx.post(f"{BASE_URL}/auth/register", json=fail_payload)
    if resp.status_code == 403:
        print("  ✓ Correct: Direct patient registration blocked.")
    else:
        print(f"  ✗ Error: Patient registration should have been blocked (Got {resp.status_code})")

    # 4. Upload Documents
    print_section("STEP 2: Uploading Documents from _documents Folder")
    
    # Map files to patients
    # We have 5 files and 5 patients.
    files = sorted([f for f in os.listdir(DOCUMENTS_DIR) if f.endswith('.pdf')])
    print(f"Found {len(files)} PDF files in {DOCUMENTS_DIR}")
    
    patient_file_map = {
        "patient1": [files[0]] if len(files) >= 1 else [],
        "patient2": [files[1]] if len(files) >= 2 else [],
        "patient3": [files[2]] if len(files) >= 3 else [],
        "patient4": [files[3]] if len(files) >= 4 else [],
        "patient5": [files[4]] if len(files) >= 5 else []
    }

    for p_key, p_files in patient_file_map.items():
        user = registered_users.get(p_key)
        # Ensure list exists
        if user and user['email'] not in patient_docs:
            patient_docs[user['email']] = []
            
        if not user:
            print(f"Skipping {p_key} (not registered)")
            continue
            
        headers = {"Authorization": f"Bearer {user['token']}"}
        
        for idx, filename in enumerate(p_files):
            filepath = os.path.join(DOCUMENTS_DIR, filename)
            print(f"{user['name']} uploading {filename}...")
            
            with open(filepath, "rb") as f:
                file_content = f.read()
                
            files_payload = {'file': (filename, io.BytesIO(file_content), 'application/pdf')}
            data_payload = {
                'category': 'LAB_REPORT', # Generic category
                'title': f"Uploaded: {filename}",
                'description': f"Test upload of {filename}"
            }
            
            try:
                resp = httpx.post(
                    f"{BASE_URL}/patient/medical-history",
                    files=files_payload,
                    data=data_payload,
                    headers=headers,
                    timeout=30.0
                )
                log_api_call("POST", "/patient/medical-history", data_payload, resp.status_code, resp.json() if resp.status_code == 201 else resp.text)
                
                if resp.status_code == 201:
                    doc = resp.json()
                    print(f"  ✓ Uploaded ID: {doc['id']}")
                    test_data["documents"].append({
                        "id": doc['id'],
                        "filename": filename,
                        "owner": user["name"]
                    })
                    # Store for AI
                    patient_docs[user['email']].append(doc['id'])
                else:
                    print(f"  ✗ Failed: {resp.text}")
            except Exception as e:
                print(f"  ✗ Exception: {str(e)}")


    # 5. Doctor Search & Appointments
    print_section("STEP 3: Doctor Search & Appointments")
    
    # Each patient requests an appointment with a different doctor
    # P1 -> D1
    # P2 -> D2
    # P3 -> D3
    # P4 -> D4
    # P5 -> D5
    
    for i in range(1, 6):
        p_key = f"patient{i}"
        d_key = f"doctor{i}"
        
        patient = registered_users.get(p_key)
        doctor = registered_users.get(d_key)
        
        if patient and doctor:
            headers = {"Authorization": f"Bearer {patient['token']}"}
            
            # Search (Verify that patient only sees their onboarding doctor)
            print(f"{patient['name']} searching for doctors...")
            s_resp = httpx.get(f"{BASE_URL}/doctors/search", headers=headers) # Generic search without query
            log_api_call("GET", "/doctors/search", {}, s_resp.status_code, s_resp.json() if s_resp.status_code == 200 else s_resp.text)
            
            if s_resp.status_code == 200:
                results = s_resp.json().get("results", [])
                print(f"  ✓ Found {len(results)} doctor(s).")
                if len(results) != 1:
                    print(f"  ⚠ Warning: Patient expected 1 doctor, got {len(results)}")
                elif results[0]["id"] != doctor["id"]:
                    print(f"  ⚠ Warning: Patient saw wrong doctor (Expected {doctor['id']}, got {results[0]['id']})")
                else:
                    print(f"  ✓ Correct: Only onboarding doctor visible.")
            
            # Specific search for the intended doctor (should work as before if it's the right doctor)
            s_resp = httpx.get(f"{BASE_URL}/doctors/search", params={"query": doctor["name"]}, headers=headers)
            log_api_call("GET", "/doctors/search", {"query": doctor["name"]}, s_resp.status_code, s_resp.json() if s_resp.status_code == 200 else s_resp.text)
            
            # Request Appt
            appt_payload = {
                "doctor_id": doctor["id"],
                "requested_date": (datetime.utcnow() + timedelta(days=i)).isoformat(),
                "reason": f"Consultation request from {patient['name']}",
                "grant_access_to_history": True
            }
            
            print(f"{patient['name']} requesting appt with {doctor['name']}...")
            resp = httpx.post(f"{BASE_URL}/appointments", json=appt_payload, headers=headers)
            log_api_call("POST", "/appointments", appt_payload, resp.status_code, resp.json() if resp.status_code == 201 else resp.text)
            
            if resp.status_code == 201:
                appt = resp.json()
                print(f"  ✓ Appt ID: {appt['id']}")
                test_data["appointments"].append({
                    "id": appt['id'],
                    "patient": patient["name"],
                    "doctor": doctor["name"],
                    "doctor_key": d_key, # for lookup later
                    "status": "pending"
                })
            else:
                 print(f"  ✗ Failed: {resp.text}")

    # 6. Doctor Actions (Approve/Reject/View)
    print_section("STEP 4: Doctor Actions")
    
    for appt_record in test_data["appointments"]:
        d_key = appt_record["doctor_key"]
        doctor = registered_users.get(d_key)
        appt_id = appt_record["id"]
        
        headers = {"Authorization": f"Bearer {doctor['token']}"}
        
        # Action logic: D2 rejects, others approve
        if d_key == "doctor2":
            # Reject
            print(f"{doctor['name']} REJECTING appt {appt_id}...")
            payload = {"status": "declined", "doctor_notes": "Cannot make it."}
            resp = httpx.patch(f"{BASE_URL}/appointments/{appt_id}/status", json=payload, headers=headers)
            log_api_call("PATCH", f"/appointments/{appt_id}/status", payload, resp.status_code, resp.json() if resp.status_code == 200 else resp.text)
            if resp.status_code == 200:
                print("  ✓ Declined")
                appt_record["status"] = "declined"
        else:
            # Approve
            print(f"{doctor['name']} APPROVING appt {appt_id}...")
            payload = {
                "appointment_time": (datetime.utcnow() + timedelta(days=5)).isoformat(),
                "doctor_notes": "See you then."
            }
            resp = httpx.post(f"{BASE_URL}/appointments/{appt_id}/approve", json=payload, headers=headers)
            log_api_call("POST", f"/appointments/{appt_id}/approve", payload, resp.status_code, resp.json() if resp.status_code == 200 else resp.text)
            
            if resp.status_code == 200:
                data = resp.json()
                print("  ✓ Approved")
                appt_record["status"] = "accepted"
                if "join_url" in data:
                    test_data["zoom_meetings"].append({
                        "appt_id": appt_id,
                        "join_url": data["join_url"]
                    })
    
    # Doctor 5 viewing records of Patient 1 (Should be forbidden if no appt, but let's test D1 viewing P1 which has appt)
    print("\nTesting Medical Record Access...")
    d1 = registered_users.get("doctor1")
    p1 = registered_users.get("patient1")
    
    if d1 and p1:
        headers = {"Authorization": f"Bearer {d1['token']}"}
        print(f"{d1['name']} viewing {p1['name']} records...")
        resp = httpx.get(f"{BASE_URL}/doctor/patients/{p1['id']}/documents", headers=headers)
        log_api_call("GET", f"/doctor/patients/{p1['id']}/documents", {}, resp.status_code, resp.json() if resp.status_code == 200 else resp.text)
        if resp.status_code == 200:
            print(f"  ✓ Access Granted. Docs found: {len(resp.json())}")
        else:
            print(f"  ✗ Access Failed: {resp.status_code}")

    # 7. Doctor Tasks
    print_section("STEP 5: Generic Doctor Tasks")
    # Create Task
    try:
        task_payload = {
            "title": "General Ward Round",
            "priority": "normal",
            "due_date": (datetime.utcnow() + timedelta(days=1)).isoformat()
        }
        resp = httpx.post(
            f"{BASE_URL}/doctor/tasks",
            json=task_payload,
            headers={"Authorization": f"Bearer {doctor_tokens[4]}"},
            timeout=30.0
        )
        log_api_call("POST", "/doctor/tasks", task_payload, resp.status_code, resp.json() if resp.status_code < 500 else resp.text)
        
        if resp.status_code == 201:
            print(f"  ✓ Task Created")
        else:
            print(f"  ✗ Task Failed: {resp.text}")
    except Exception as e:
        print(f"  ✗ Exception: {str(e)}")

    print_section("STEP 6: AI Workflow Integration")

    # Pick Patient 1 and Doctor 1 (who has access via appointment)
    p1_email = users_config[0]['email']
    d1_email = users_config[5]['email'] # Doctor 1 is at index 5 effectively
    
    p1_token = registered_users[p1_email]['token']
    d1_token = registered_users[d1_email]['token']
    p1_id = registered_users[p1_email]['id']
    
    # Get a document ID from Patient 1
    p1_docs = patient_docs.get(p1_email, [])
    if not p1_docs:
        print("  ⚠ No documents found for Patient 1. Skipping AI Queue test.")
    else:
        doc_id = p1_docs[0]
        print(f"Using Document ID: {doc_id} for Patient 1")

        # 1. Doctor Queues Document for Processing
        print("\n[AI] Doctor 1 requesting document processing...")
        try:
            process_payload = {
                "patient_id": p1_id,
                "document_id": doc_id,
                "processing_type": "comprehensive",
                "priority": "normal"
            }
            resp = httpx.post(
                f"{BASE_URL}/doctor/ai/process-document",
                json=process_payload,
                headers={"Authorization": f"Bearer {d1_token}"},
                timeout=30.0
            )
            log_api_call("POST", "/doctor/ai/process-document", process_payload, resp.status_code, resp.json() if resp.status_code < 500 else resp.text)
            
            if resp.status_code == 201:
                print(f"  ✓ AI Processing Queued")
            else:
                print(f"  ✗ Failed to Queue: {resp.text}")
        except Exception as e:
            print(f"  ✗ Exception: {str(e)}")

        print(f"  ... Waiting for background processing (polling up to 5 mins) ...")
        # Polling for processing completion
        import time
        max_attempts = 60
        processed = False
        for attempt in range(max_attempts):
            time.sleep(5)
            # Check status via doctor's document list
            try:
                doc_resp = httpx.get(
                    f"{BASE_URL}/doctor/patients/{p1_id}/documents",
                    headers={"Authorization": f"Bearer {d1_token}"},
                    timeout=10.0
                )
                if doc_resp.status_code == 200:
                    docs = doc_resp.json()
                    for d in docs:
                        if d["id"] == doc_id:
                            # Assuming total_chunks or processing_details tells us it's done
                            # Our processor sets processing_details[tier_3_vision][status] = completed
                            # or just check total_chunks
                            if d.get("total_chunks", 0) > 0:
                                print(f"  ✓ Processing Complete! Chunks found: {d['total_chunks']}")
                                processed = True
                                break
                if processed: break
                print(f"  ... still processing (attempt {attempt+1}/{max_attempts}) ...")
            except Exception as e:
                print(f"  ✗ Polling error: {e}")
        
        if not processed:
            print("  ⚠ Processing timed out or failed to produce chunks. Continuing anyway...")

        # 2. Patient Chats with AI
        print("\n[AI] Patient 1 chatting with AI...")
        try:
            chat_payload = {
                "patient_id": p1_id,
                "query": "What does my report say about heart rate?",
                "document_id": doc_id
            }
            # Stream response - for test we just get text
            # Using httpx to consume stream
            async def test_chat_stream(): # Helper to consume stream synchronously in this context
                client = httpx.Client()
                result_text = ""
                with client.stream(
                    "POST", 
                    f"{BASE_URL}/doctor/ai/chat/patient", 
                    json=chat_payload, 
                    headers={"Authorization": f"Bearer {p1_token}"},
                    timeout=30.0
                ) as response:
                    log_api_call("POST", "/doctor/ai/chat/patient", chat_payload, response.status_code, "STREAM_CONTENT")
                    if response.status_code == 200:
                        for chunk in response.iter_text():
                            result_text += chunk
                        print(f"  ✓ Chat Response: {result_text[:100]}...") # Truncate for display
                    else:
                        print(f"  ✗ Chat Failed: {response.text}")
                        # response.read()
            
            # Since we are in sync function, we use synchronous httpx client logic
            with httpx.Client() as client:
                resp = client.post(
                    f"{BASE_URL}/doctor/ai/chat/patient",
                    json=chat_payload,
                    headers={"Authorization": f"Bearer {p1_token}"},
                    timeout=60.0
                )
                log_api_call("POST", "/doctor/ai/chat/patient", chat_payload, resp.status_code, resp.text)
                if resp.status_code == 200:
                    print(f"  ✓ Patient Chat Success")
                else:
                    print(f"  ✗ Patient Chat Failed: {resp.text}")

        except Exception as e:
            print(f"  ✗ Exception: {str(e)}")

        # 3. Doctor Chats with AI
        print("\n[AI] Doctor 1 chatting with AI about Patient 1...")
        try:
            doc_chat_payload = {
                "patient_id": p1_id,
                "query": "Summarize this patient's condition.",
                "document_id": doc_id
            }
            with httpx.Client() as client:
                resp = client.post(
                    f"{BASE_URL}/doctor/ai/chat/doctor",
                    json=doc_chat_payload,
                    headers={"Authorization": f"Bearer {d1_token}"},
                    timeout=60.0
                )
                log_api_call("POST", "/doctor/ai/chat/doctor", doc_chat_payload, resp.status_code, resp.text)
                if resp.status_code == 200:
                    print(f"  ✓ Doctor Chat Success")
                else:
                    print(f"  ✗ Doctor Chat Failed: {resp.text}")

        except Exception as e:
            print(f"  ✗ Exception: {str(e)}")
    generate_report()

def generate_report():
    print_section("GENERATING REPORT")
    
    report_content = f"# E2E Test Report\n\nGenerated: {datetime.now().isoformat()}\n\n"
    report_content += "## Summary\n"
    report_content += f"- Users Created: {len(test_data['users'])}\n"
    report_content += f"- Documents Uploaded: {len(test_data['documents'])}\n"
    report_content += f"- Appointments: {len(test_data['appointments'])}\n\n"
    
    report_content += "## JSON Data Used & API Interactions\n\n"
    
    # Dump the raw log of interactions
    report_content += "```json\n"
    report_content += json.dumps(test_data["endpoint_calls"], indent=2)
    report_content += "\n```\n"

    report_path = "USER_REQUEST_REPORT.md"
    with open(report_path, "w") as f:
        f.write(report_content)
        
    print(f"Report saved to {report_path}")

if __name__ == "__main__":
    run_custom_e2e_test()
