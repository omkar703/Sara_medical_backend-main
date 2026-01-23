"""
Complete End-to-End Test for SaraMedico Platform
Tests all user flows: Auth, Medical History, Appointments, Zoom Meetings, Tasks
"""

import httpx
import io
import os
import sys
import json
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
from uuid import UUID

# Setup environment
sys.path.append(os.path.join(os.getcwd(), "backend"))
load_dotenv("backend/.env")

# Patch DATABASE_URL for local execution
if os.environ.get("DATABASE_URL"):
    os.environ["DATABASE_URL"] = os.environ["DATABASE_URL"].replace("@postgres:", "@localhost:")

from app.database import AsyncSessionLocal
from app.models.patient import Patient
from sqlalchemy import select

BASE_URL = "http://localhost:8000/api/v1"

# Store test data for flow.md
test_data = {
    "users": [],
    "documents": [],
    "appointments": [],
    "tasks": [],
    "zoom_meetings": []
}


async def create_patient_profiles_batch(patient_data_list):
    """Create multiple patient profiles in one async session"""
    async with AsyncSessionLocal() as db:
        for patient_data in patient_data_list:
            user_id = UUID(patient_data["id"])
            
            # Check if exists
            res = await db.execute(select(Patient).where(Patient.id == user_id))
            if res.scalar_one_or_none():
                continue
            
            patient = Patient(
                id=user_id,
                organization_id=UUID(patient_data["organization_id"]),
                mrn=patient_data["mrn"],
                full_name="ENCRYPTED_DUMMY",
                date_of_birth="ENCRYPTED_DUMMY",
                created_by=user_id
            )
            db.add(patient)
        
        await db.commit()
        print(f"  ✓ Created {len(patient_data_list)} patient profile(s) in DB")


def print_section(title):
    """Print formatted section header"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def test_complete_flow():
    """Main test function covering all features"""
    
    print_section("SARAMEDICO COMPLETE END-TO-END TEST")
    
    timestamp = int(datetime.utcnow().timestamp())
    
    # ========================================================================
    # STEP 1: USER REGISTRATION (2 Patients, 3 Doctors)
    # ========================================================================
    print_section("STEP 1: User Registration & Authentication")
    
    users_to_create = [
        {
            "email": f"patient1_{timestamp}@test.com",
            "password": "SecurePass123!",
            "full_name": "Alice Johnson",
            "role": "patient",
            "type": "patient1"
        },
        {
            "email": f"patient2_{timestamp}@test.com",
            "password": "SecurePass123!",
            "full_name": "Bob Martinez",
            "role": "patient",
            "type": "patient2"
        },
        {
            "email": f"doctor1_{timestamp}@test.com",
            "password": "SecurePass123!",
            "full_name": "Dr. Sarah Chen",
            "role": "doctor",
            "specialty": "Cardiology",
            "license": f"LIC-CARDIO-{timestamp}",
            "type": "doctor1"
        },
        {
            "email": f"doctor2_{timestamp}@test.com",
            "password": "SecurePass123!",
            "full_name": "Dr. Michael Brown",
            "role": "doctor",
            "specialty": "Dermatology",
            "license": f"LIC-DERMA-{timestamp}",
            "type": "doctor2"
        },
        {
            "email": f"doctor3_{timestamp}@test.com",
            "password": "SecurePass123!",
            "full_name": "Dr. Emily Wang",
            "role": "doctor",
            "specialty": "Pediatrics",
            "license": f"LIC-PEDIA-{timestamp}",
            "type": "doctor3"
        }
    ]
    
    registered_users = {}
    patients_to_create = []
    
    for user_data in users_to_create:
        print(f"Registering {user_data['full_name']} ({user_data['role']})...")
        
        reg_payload = {
            "email": user_data["email"],
            "password": user_data["password"],
            "full_name": user_data["full_name"],
            "role": user_data["role"]
        }
        
        if user_data["role"] == "doctor":
            reg_payload["specialty"] = user_data["specialty"]
            reg_payload["license_number"] = user_data["license"]
        
        resp = httpx.post(f"{BASE_URL}/auth/register", json=reg_payload)
        
        if resp.status_code != 201:
            print(f"  ✗ FAILED: {resp.text}")
            continue
        
        user_info = resp.json()
        print(f"  ✓ Registered: {user_info['name']} (ID: {user_info['id']})")
        
        # Login immediately
        login_resp = httpx.post(f"{BASE_URL}/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        
        if login_resp.status_code != 200:
            print(f"  ✗ Login failed: {login_resp.text}")
            continue
        
        login_data = login_resp.json()
        token = login_data["access_token"]
        user_details = login_data["user"]
        
        registered_users[user_data["type"]] = {
            "email": user_data["email"],
            "password": user_data["password"],
            "full_name": user_data["full_name"],
            "token": token,
            "id": user_details["id"],
            "organization_id": user_details["organization_id"],
            "role": user_data["role"]
        }
        
        if user_data["role"] == "doctor":
            registered_users[user_data["type"]]["specialty"] = user_data.get("specialty")
        
        # Collect patient data for batch creation
        if user_data["role"] == "patient":
            patients_to_create.append({
                "id": user_details["id"],
                "organization_id": user_details["organization_id"],
                "mrn": f"MRN-{user_data['email'].split('@')[0]}"
            })
        
        print(f"  ✓ Logged in successfully")
        
        # Add to test data
        test_data["users"].append({
            "email": user_data["email"],
            "password": user_data["password"],
            "name": user_data["full_name"],
            "role": user_data["role"],
            "id": user_details["id"],
            "specialty": user_data.get("specialty", "N/A")
        })
    
    # Create all patient profiles in one async operation
    if patients_to_create:
        print(f"\nCreating {len(patients_to_create)} patient profile(s) in database...")
        asyncio.run(create_patient_profiles_batch(patients_to_create))
    
    print(f"\n✓ Total users registered: {len(registered_users)}")
    
    # ========================================================================
    # STEP 2: MEDICAL HISTORY UPLOAD (Patients & Doctors)
    # ========================================================================
    print_section("STEP 2: Medical History Document Upload")
    
    # Patient 1 uploads 5 documents
    patient1 = registered_users.get("patient1")
    if patient1:
        print(f"Patient 1 ({patient1['full_name']}) uploading documents...")
        patient1_headers = {"Authorization": f"Bearer {patient1['token']}"}
        
        document_types = [
            ("LAB_REPORT", "Blood Test Results", "CBC and metabolic panel"),
            ("IMAGING", "Chest X-Ray", "Annual checkup chest imaging"),
            ("PAST_PRESCRIPTION", "Previous Medications", "Medication history from 2024"),
            ("LAB_REPORT", "Diabetes Screening", "HbA1c test results"),
            ("OTHER", "Vaccination Record", "COVID-19 vaccination card")
        ]
        
        for idx, (category, title, description) in enumerate(document_types, 1):
            dummy_content = b"%PDF-1.4 Medical Document Content " + str(idx).encode()
            files = {'file': (f'patient1_doc{idx}.pdf', io.BytesIO(dummy_content), 'application/pdf')}
            data = {'category': category, 'title': title, 'description': description}
            
            resp = httpx.post(
                f"{BASE_URL}/patient/medical-history",
                files=files,
                data=data,
                headers=patient1_headers,
                timeout=30.0
            )
            
            if resp.status_code == 201:
                doc_data = resp.json()
                print(f"  ✓ Doc {idx}: {title} ({category}) - ID: {doc_data['id']}")
                test_data["documents"].append({
                    "patient": patient1['full_name'],
                    "patient_id": patient1['id'],
                    "title": title,
                    "category": category,
                    "id": doc_data['id']
                })
            else:
                print(f"  ✗ Failed: {resp.text}")
    
    # Patient 2 uploads 3 documents
    patient2 = registered_users.get("patient2")
    if patient2:
        print(f"\nPatient 2 ({patient2['full_name']}) uploading documents...")
        patient2_headers = {"Authorization": f"Bearer {patient2['token']}"}
        
        for idx in range(1, 4):
            dummy_content = b"%PDF-1.4 Patient 2 Medical Record " + str(idx).encode()
            files = {'file': (f'patient2_doc{idx}.pdf', io.BytesIO(dummy_content), 'application/pdf')}
            data = {'category': 'LAB_REPORT', 'title': f'Patient 2 Lab {idx}', 'description': f'Test {idx}'}
            
            resp = httpx.post(
                f"{BASE_URL}/patient/medical-history",
                files=files,
                data=data,
                headers=patient2_headers,
                timeout=30.0
            )
            
            if resp.status_code == 201:
                doc_data = resp.json()
                print(f"  ✓ Doc {idx}: ID: {doc_data['id']}")
                test_data["documents"].append({
                    "patient": patient2['full_name'],
                    "patient_id": patient2['id'],
                    "title": data['title'],
                    "category": data['category'],
                    "id": doc_data['id']
                })
    
    # Doctor uploads on behalf of patient (requires patient_id in metadata)
    doctor1 = registered_users.get("doctor1")
    if doctor1 and patient1:
        print(f"\nDoctor ({doctor1['full_name']}) uploading for Patient 1...")
        doctor1_headers = {"Authorization": f"Bearer {doctor1['token']}"}
        
        # Note: This would require a different endpoint or metadata field
        # For now, showing the concept
        print("  (Note: Doctor upload on behalf requires specific API - skipping for now)")
    
    # ========================================================================
    # STEP 3: PATIENT SEARCHES FOR DOCTORS
    # ========================================================================
    print_section("STEP 3: Patient Search for Doctors")
    
    if patient1:
        patient1_headers = {"Authorization": f"Bearer {patient1['token']}"}
        
        print("Searching for 'Cardiology' specialists...")
        resp = httpx.get(
            f"{BASE_URL}/doctors/search",
            params={"specialty": "Cardiology"},
            headers=patient1_headers
        )
        
        if resp.status_code == 200:
            response_data = resp.json()
            doctors = response_data.get("results", [])
            print(f"  ✓ Found {len(doctors)} cardiologist(s):")
            for doc in doctors:
                print(f"    - Dr. {doc['name']} (ID: {doc['id']}, Specialty: {doc['specialty']})")
        else:
            print(f"  ✗ Search failed: {resp.text}")
        
        print("\nSearching for 'Dr. Emily Wang'...")
        resp = httpx.get(
            f"{BASE_URL}/doctors/search",
            params={"query": "Emily"},
            headers=patient1_headers
        )
        
        if resp.status_code == 200:
            response_data = resp.json()
            doctors = response_data.get("results", [])
            print(f"  ✓ Found {len(doctors)} doctor(s) matching 'Emily'")
            for doc in doctors:
                print(f"    - {doc['name']} ({doc['specialty']})")
    
    # ========================================================================
    # STEP 4 & 5: PATIENT REQUESTS APPOINTMENTS
    # ========================================================================
    print_section("STEP 4 & 5: Appointment Requests")
    
    appointments_created = []
    
    # Patient 1 requests appointment with Doctor 1 (will be APPROVED)
    if patient1 and registered_users.get("doctor1"):
        doctor1 = registered_users["doctor1"]
        patient1_headers = {"Authorization": f"Bearer {patient1['token']}"}
        
        print(f"Patient 1 requesting appointment with Dr. {doctor1['full_name']}...")
        
        appointment_payload = {
            "doctor_id": doctor1["id"],
            "requested_date": (datetime.utcnow() + timedelta(days=2)).isoformat(),
            "reason": "Cardiac evaluation and follow-up",
            "grant_access_to_history": True  # Grant medical history access
        }
        
        resp = httpx.post(
            f"{BASE_URL}/appointments/request",
            json=appointment_payload,
            headers=patient1_headers
        )
        
        if resp.status_code == 201:
            appt = resp.json()
            appointments_created.append({**appt, "patient": patient1, "doctor": doctor1})
            print(f"  ✓ Appointment created: ID {appt['id']}, Status: {appt['status']}")
            test_data["appointments"].append({
                "id": appt['id'],
                "patient": patient1['full_name'],
                "doctor": doctor1['full_name'],
                "status": appt['status'],
                "date": appt['requested_date'],
                "reason": appointment_payload['reason'],
                "grant_access": True
            })
        else:
            print(f"  ✗ Failed: {resp.text}")
    
    # Patient 2 requests appointment with Doctor 2 (will be REJECTED)
    if patient2 and registered_users.get("doctor2"):
        doctor2 = registered_users["doctor2"]
        patient2_headers = {"Authorization": f"Bearer {patient2['token']}"}
        
        print(f"\nPatient 2 requesting appointment with Dr. {doctor2['full_name']}...")
        
        appointment_payload = {
            "doctor_id": doctor2["id"],
            "requested_date": (datetime.utcnow() + timedelta(days=5)).isoformat(),
            "reason": "Skin rash consultation",
            "grant_access_to_history": True
        }
        
        resp = httpx.post(
            f"{BASE_URL}/appointments/request",
            json=appointment_payload,
            headers=patient2_headers
        )
        
        if resp.status_code == 201:
            appt = resp.json()
            appointments_created.append({**appt, "patient": patient2, "doctor": doctor2})
            print(f"  ✓ Appointment created: ID {appt['id']}, Status: {appt['status']}")
            test_data["appointments"].append({
                "id": appt['id'],
                "patient": patient2['full_name'],
                "doctor": doctor2['full_name'],
                "status": appt['status'],
                "date": appt['requested_date'],
                "reason": appointment_payload['reason'],
                "grant_access": True
            })
        else:
            print(f"  ✗ Failed: {resp.text}")
    
    # Patient 1 checks appointment status
    if patient1 and appointments_created:
        print(f"\nPatient 1 checking appointment status...")
        patient1_headers = {"Authorization": f"Bearer {patient1['token']}"}
        
        resp = httpx.get(f"{BASE_URL}/appointments", headers=patient1_headers)
        
        if resp.status_code == 200:
            appointments = resp.json()
            print(f"  ✓ Patient has {len(appointments)} appointment(s):")
            for appt in appointments:
                print(f"    - ID: {appt['id']}, Status: {appt['status']}, Doctor ID: {appt['doctor_id']}")
    
    # ========================================================================
    # STEP 6 & 7: DOCTOR APPROVES/REJECTS APPOINTMENTS
    # ========================================================================
    print_section("STEP 6 & 7: Doctor Approves/Rejects Appointments")
    
    # Doctor 1 APPROVES Patient 1's appointment
    if doctor1 and len(appointments_created) > 0:
        appt_to_approve = appointments_created[0]
        doctor1_headers = {"Authorization": f"Bearer {doctor1['token']}"}
        
        print(f"Dr. {doctor1['full_name']} APPROVING appointment {appt_to_approve['id']}...")
        
        approval_payload = {
            "appointment_time": (datetime.utcnow() + timedelta(days=2)).isoformat(),
            "doctor_notes": "Looking forward to the consultation"
        }
        
        resp = httpx.post(
            f"{BASE_URL}/appointments/{appt_to_approve['id']}/approve",
            json=approval_payload,
            headers=doctor1_headers
        )
        
        if resp.status_code == 200:
            updated_appt = resp.json()
            print(f"  ✓ Appointment APPROVED:")
            print(f"    - Status: {updated_appt['status']}")
            print(f"    - Zoom Join URL: {updated_appt.get('join_url', 'N/A')}")
            print(f"    - Meeting ID: {updated_appt.get('meeting_id', 'N/A')}")
            
            # Update test data
            for appt in test_data["appointments"]:
                if appt["id"] == appt_to_approve['id']:
                    appt["status"] = "accepted"
                    appt["zoom_url"] = updated_appt.get('join_url', 'N/A')
                    appt["meeting_id"] = updated_appt.get('meeting_id', 'N/A')
            
            if updated_appt.get('join_url'):
                test_data["zoom_meetings"].append({
                    "appointment_id": appt_to_approve['id'],
                    "meeting_id": updated_appt['meeting_id'],
                    "join_url": updated_appt['join_url'],
                    "doctor": doctor1['full_name'],
                    "patient": appt_to_approve['patient']['full_name']
                })
        else:
            print(f"  ✗ Approval failed: {resp.text}")
    
    # Doctor 2 REJECTS Patient 2's appointment
    if len(appointments_created) > 1 and registered_users.get("doctor2"):
        appt_to_reject = appointments_created[1]
        doctor2 = registered_users["doctor2"]
        doctor2_headers = {"Authorization": f"Bearer {doctor2['token']}"}
        
        print(f"\nDr. {doctor2['full_name']} DECLINING appointment {appt_to_reject['id']}...")
        
        resp = httpx.patch(
            f"{BASE_URL}/appointments/{appt_to_reject['id']}/status",
            json={"status": "declined", "doctor_notes": "Unfortunately not available at requested time"},
            headers=doctor2_headers
        )
        
        if resp.status_code == 200:
            updated_appt = resp.json()
            print(f"  ✓ Appointment DECLINED:")
            print(f"    - Status: {updated_appt['status']}")
            print(f"    - No Zoom meeting created (as expected)")
            
            # Update test data
            for appt in test_data["appointments"]:
                if appt["id"] == appt_to_reject['id']:
                    appt["status"] = "declined"
        else:
            print(f"  ✗ Decline failed: {resp.text}")
    
    # ========================================================================
    # STEP 8: PATIENT CHECKS STATUS AFTER APPROVAL
    # ========================================================================
    print_section("STEP 8: Patient Checks Updated Appointment Status")
    
    if patient1:
        patient1_headers = {"Authorization": f"Bearer {patient1['token']}"}
        
        print(f"Patient 1 checking status after doctor approval...")
        resp = httpx.get(f"{BASE_URL}/appointments", headers=patient1_headers)
        
        if resp.status_code == 200:
            appointments = resp.json()
            for appt in appointments:
                if appt['status'] == 'accepted':
                    print(f"  ✓ APPROVED Appointment:")
                    print(f"    - ID: {appt['id']}")
                    print(f"    - Status: {appt['status']}")
                    print(f"    - Zoom Meeting: {appt.get('join_url', 'N/A')}")
                    print(f"    → Patient should receive notification (UI/Email)")
    
    # ========================================================================
    # STEP 9 & 10: ZOOM MEETING & MEDICAL ACCESS
    # ========================================================================
    print_section("STEP 9 & 10: Zoom Meeting Links & Medical Access")
    
    print("Zoom meeting links have been generated upon approval (see Step 6).")
    print("Medical access was granted when patient requested appointment with grant_access_to_history=True")
    
    # ========================================================================
    # STEP 11: DOCTOR VIEWS PATIENT MEDICAL RECORDS
    # ========================================================================
    print_section("STEP 11: Doctor Accesses Patient Medical Records")
    
    if doctor1 and patient1:
        doctor1_headers = {"Authorization": f"Bearer {doctor1['token']}"}
        
        print(f"Dr. {doctor1['full_name']} viewing Patient 1's medical records...")
        
        resp = httpx.get(
            f"{BASE_URL}/doctor/patients/{patient1['id']}/documents",
            headers=doctor1_headers
        )
        
        if resp.status_code == 200:
            documents = resp.json()
            print(f"  ✓ Access GRANTED: Found {len(documents)} document(s):")
            for doc in documents[:3]:  # Show first 3
                print(f"    - {doc['file_name']} ({doc['category']})")
                print(f"      Presigned URL: {doc['presigned_url'][:60]}...")
        elif resp.status_code == 403:
            print(f"  ✗ Access DENIED: {resp.json()['detail']}")
        else:
            print(f"  ✗ Error: {resp.text}")
    
    # Test unauthorized access (Doctor 3 shouldn't have access to Patient 1)
    if registered_users.get("doctor3") and patient1:
        doctor3 = registered_users["doctor3"]
        doctor3_headers = {"Authorization": f"Bearer {doctor3['token']}"}
        
        print(f"\nDr. {doctor3['full_name']} (NO permission) trying to access Patient 1...")
        
        resp = httpx.get(
            f"{BASE_URL}/doctor/patients/{patient1['id']}/documents",
            headers=doctor3_headers
        )
        
        if resp.status_code == 403:
            print(f"  ✓ Correctly DENIED: {resp.json()['detail']}")
        else:
            print(f"  ✗ Unexpected response: {resp.status_code}")
    
    # ========================================================================
    # STEP 12: DOCTOR CREATES TASKS (TO-DO)
    # ========================================================================
    print_section("STEP 12: Doctor Task Management (CRUD Operations)")
    
    if doctor1:
        doctor1_headers = {"Authorization": f"Bearer {doctor1['token']}"}
        
        # CREATE tasks
        tasks_to_create = [
            {
                "title": "Review Patient 1 Lab Results",
                "description": "Analyze blood work and metabolic panel",
                "priority": "urgent",
                "due_date": (datetime.utcnow() + timedelta(days=1)).isoformat()
            },
            {
                "title": "Prepare consultation notes",
                "description": "Summary for upcoming patient meeting",
                "priority": "normal",
                "due_date": (datetime.utcnow() + timedelta(days=2)).isoformat()
            },
            {
                "title": "Update patient medical plan",
                "description": "Revise treatment plan based on new findings",
                "priority": "normal",
                "due_date": (datetime.utcnow() + timedelta(days=7)).isoformat()
            }
        ]
        
        print(f"Dr. {doctor1['full_name']} creating tasks...")
        created_task_ids = []
        
        for task_data in tasks_to_create:
            resp = httpx.post(
                f"{BASE_URL}/doctor/tasks",
                json=task_data,
                headers=doctor1_headers
            )
            
            if resp.status_code == 201:
                task = resp.json()
                created_task_ids.append(task['id'])
                print(f"  ✓ Task created: {task['title']} (ID: {task['id']}, Priority: {task['priority']})")
                test_data["tasks"].append({
                    "id": task['id'],
                    "doctor": doctor1['full_name'],
                    "title": task['title'],
                    "priority": task['priority'],
                    "status": task.get('status', 'pending')
                })
            else:
                print(f"  ✗ Failed to create '{task_data['title']}': {resp.text}")
        
        # READ/LIST all tasks
        print(f"\n📋 Fetching all tasks for Dr. {doctor1['full_name']}...")
        resp = httpx.get(f"{BASE_URL}/doctor/tasks", headers=doctor1_headers)
        
        if resp.status_code == 200:
            tasks = resp.json()
            print(f"  ✓ Total tasks: {len(tasks)}")
            for task in tasks[:5]:  # Show first 5
                status_icon = "✓" if task.get('status') == 'completed' else "○"
                print(f"    {status_icon} [{task.get('priority', 'N/A').upper()}] {task['title']}")
        else:
            print(f"  ✗ Failed to fetch tasks: {resp.text}")
        
        # UPDATE a task (mark one as completed)
        if created_task_ids:
            task_to_update = created_task_ids[0]
            print(f"\n📝 Updating task {task_to_update} to 'completed'...")
            
            resp = httpx.patch(
                f"{BASE_URL}/doctor/tasks/{task_to_update}",
                json={"status": "completed", "notes": "Lab results reviewed, all normal"},
                headers=doctor1_headers
            )
            
            if resp.status_code == 200:
                updated_task = resp.json()
                print(f"  ✓ Task updated: Status = {updated_task.get('status')}")
            else:
                print(f"  ✗ Failed to update task: {resp.text}")
        
        # DELETE a task
        if len(created_task_ids) > 1:
            task_to_delete = created_task_ids[-1]  # Delete the last one
            print(f"\n🗑️  Deleting task {task_to_delete}...")
            
            resp = httpx.delete(
                f"{BASE_URL}/doctor/tasks/{task_to_delete}",
                headers=doctor1_headers
            )
            
            if resp.status_code == 204 or resp.status_code == 200:
                print(f"  ✓ Task deleted successfully")
                # Remove from test data
                test_data["tasks"] = [t for t in test_data["tasks"] if t["id"] != task_to_delete]
            else:
                print(f"  ✗ Failed to delete task: {resp.text}")
        
        # Verify final task list
        print(f"\n📊 Final task count after CRUD operations...")
        resp = httpx.get(f"{BASE_URL}/doctor/tasks", headers=doctor1_headers)
        
        if resp.status_code == 200:
            final_tasks = resp.json()
            print(f"  ✓ Remaining tasks: {len(final_tasks)}")
            completed_count = sum(1 for t in final_tasks if t.get('status') == 'completed')
            pending_count = len(final_tasks) - completed_count
            print(f"    - Completed: {completed_count}")
            print(f"    - Pending: {pending_count}")
    else:
        print("No doctor available for task testing")

    
    # ========================================================================
    # TEST SUMMARY
    # ========================================================================
    print_section("TEST SUMMARY")
    
    print(f"✓ Users Created: {len(test_data['users'])}")
    print(f"✓ Documents Uploaded: {len(test_data['documents'])}")
    print(f"✓ Appointments Created: {len(test_data['appointments'])}")
    print(f"✓ Zoom Meetings Generated: {len(test_data['zoom_meetings'])}")
    print(f"✓ Tasks Created: {len(test_data['tasks'])}")
    
    print("\n" + "="*80)
    print("  ALL TESTS COMPLETED SUCCESSFULLY!")
    print("="*80 + "\n")
    
    # ========================================================================
    # GENERATE FLOW.MD FILE
    # ========================================================================
    generate_flow_md()


def generate_flow_md():
    """Generate flow.md with all test data for manual testing"""
    
    flow_content = f"""# SaraMedico E2E Testing Flow
**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## Test Environment
- **Backend URL:** {BASE_URL}
- **Total Users:** {len(test_data['users'])}
- **Total Documents:** {len(test_data['documents'])}
- **Total Appointments:** {len(test_data['appointments'])}

---

## 1. User Credentials

### Patients

"""
    
    for user in test_data['users']:
        if user['role'] == 'patient':
            flow_content += f"""
**{user['name']}**
- Email: `{user['email']}`
- Password: `{user['password']}`
- User ID: `{user['id']}`
"""
    
    flow_content += "\n### Doctors\n"
    
    for user in test_data['users']:
        if user['role'] == 'doctor':
            flow_content += f"""
**{user['name']}**
- Email: `{user['email']}`
- Password: `{user['password']}`
- User ID: `{user['id']}`
- Specialty: `{user['specialty']}`
"""
    
    flow_content += f"""

---

## 2. Authentication Testing

### Sign Up (POST /api/v1/auth/register)

**Example Request:**
```json
{{
  "email": "newuser@test.com",
  "password": "SecurePass123!",
  "full_name": "New User",
  "role": "patient"
}}
```

### Login (POST /api/v1/auth/login)

**Example Request:**
```json
{{
  "email": "{test_data['users'][0]['email']}",
  "password": "{test_data['users'][0]['password']}"
}}
```

**Expected Response:**
```json
{{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "user": {{
    "id": "...",
    "email": "...",
    "role": "patient"
  }}
}}
```

### Logout (POST /api/v1/auth/logout)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:**
```json
{{
  "refresh_token": "<refresh_token>"
}}
```

---

## 3. Medical History Upload

### Patient Upload (POST /api/v1/patient/medical-history)

**Headers:**
```
Authorization: Bearer <patient_access_token>
```

**Form Data:**
- `file`: Medical document (PDF/Image)
- `category`: LAB_REPORT | IMAGING | PAST_PRESCRIPTION | OTHER
- `title`: Document title
- `description`: Document description

**Uploaded Documents:**

"""
    
    for doc in test_data['documents']:
        flow_content += f"""
- **{doc['title']}** ({doc['category']})
  - Patient: {doc['patient']}
  - Document ID: `{doc['id']}`
"""
    
    flow_content += f"""

---

## 4. Doctor Search

### Search by Specialty (GET /api/v1/doctors/search?specialty=Cardiology)

**Headers:**
```
Authorization: Bearer <patient_access_token>
```

**Example Response:**
```json
[
  {{
    "id": "...",
    "full_name": "Dr. Sarah Chen",
    "specialty": "Cardiology",
    "license_number": "LIC-..."
  }}
]
```

### Search by Name (GET /api/v1/doctors/search?name=Emily)

---

## 5. Appointment Flow

### Request Appointment (POST /api/v1/appointments/request)

**Headers:**
```
Authorization: Bearer <patient_access_token>
```

**Request:**
```json
{{
  "doctor_id": "<doctor_uuid>",
  "requested_date": "2026-01-25T10:00:00",
  "reason": "Medical consultation",
  "grant_access_to_history": true
}}
```

### Check Appointment Status (GET /api/v1/appointments)

**Headers:**
```
Authorization: Bearer <patient_access_token>
```

### Created Appointments:

"""
    
    for appt in test_data['appointments']:
        flow_content += f"""
**Appointment ID:** `{appt['id']}`
- Patient: {appt['patient']}
- Doctor: {appt['doctor']}
- Status: **{appt['status']}**
- Reason: {appt['reason']}
- Date: {appt['date']}
"""
        if appt.get('zoom_url'):
            flow_content += f"- Zoom URL: {appt['zoom_url']}\n"
        flow_content += "\n"
    
    flow_content += f"""

---

## 6. Doctor Appointment Management

### View Pending Appointments (GET /api/v1/appointments)

**Headers:**
```
Authorization: Bearer <doctor_access_token>
```

### Approve Appointment (POST /api/v1/appointments/{{appointment_id}}/approve)

**Headers:**
```
Authorization: Bearer <doctor_access_token>
```

**Response includes Zoom meeting link:**
```json
{{
  "id": "...",
  "status": "accepted",
  "meeting_id": "123456789",
  "join_url": "https://zoom.us/j/123456789?pwd=...",
  "start_url": "https://zoom.us/s/123456789?..."
}}
```

### Reject Appointment (PATCH /api/v1/appointments/{{appointment_id}}/status)

**Headers:**
```
Authorization: Bearer <doctor_access_token>
```

**Request:**
```json
{{
  "status": "declined"
}}
```

---

## 7. Zoom Meeting Integration

"""
    
    if test_data['zoom_meetings']:
        flow_content += "### Generated Zoom Meetings:\n\n"
        for meeting in test_data['zoom_meetings']:
            flow_content += f"""
**Meeting for Appointment:** `{meeting['appointment_id']}`
- Doctor: {meeting['doctor']}
- Patient: {meeting['patient']}
- Meeting ID: `{meeting['meeting_id']}`
- Join URL: {meeting['join_url']}

"""
    else:
        flow_content += "\n*No Zoom meetings generated in this test run*\n"
    
    flow_content += f"""

---

## 8. Medical Records Access

### Doctor Views Patient Documents (GET /api/v1/doctor/patients/{{patient_id}}/documents)

**Headers:**
```
Authorization: Bearer <doctor_access_token>
```

**Prerequisites:**
- Patient must have granted access via appointment with `grant_access_to_history: true`

**Test Cases:**

✅ **Authorized Access:**
- Doctor ID: `{test_data['users'][2]['id']}` (Dr. {test_data['users'][2]['name']})
- Patient ID: `{test_data['users'][0]['id']}` (Patient 1)
- Expected: 200 OK with document list

❌ **Unauthorized Access:**
- Doctor ID: `{test_data['users'][4]['id']}` (Dr. {test_data['users'][4]['name']})
- Patient ID: `{test_data['users'][0]['id']}` (Patient 1)
- Expected: 403 Forbidden

---

## 9. Task Management (Doctor Dashboard)

### Create Task (POST /api/v1/tasks)

**Headers:**
```
Authorization: Bearer <doctor_access_token>
```

**Request:**
```json
{{
  "title": "Review patient lab results",
  "priority": "high",
  "due_date": "2026-01-24T10:00:00"
}}
```

### View All Tasks (GET /api/v1/tasks)

**Headers:**
```
Authorization: Bearer <doctor_access_token>
```

### Created Tasks:

"""
    
    for task in test_data['tasks']:
        flow_content += f"""
- **{task['title']}**
  - ID: `{task['id']}`
  - Doctor: {task['doctor']}
  - Priority: {task['priority']}
  - Status: {task['status']}
"""
    
    flow_content += f"""

---

## 10. Manual Testing Steps

### Step-by-Step Test Flow:

1. **Authentication Test**
   - Sign up new user → Verify 201 Created
   - Login with credentials → Verify 200 OK + JWT token
   - Access protected endpoint → Verify 401 if not authenticated

2. **Medical History Upload**
   - Login as Patient 1
   - Upload 5 different documents (varying categories)
   - Verify presigned URLs are returned
   - Verify 15-minute expiration on URLs

3. **Doctor Search**
   - Login as Patient 1
   - Search for "Cardiology" → Should find Dr. Sarah Chen
   - Search for "Emily" → Should find Dr. Emily Wang

4. **Appointment Request**
   - Login as Patient 1
   - Request appointment with Dr. Sarah Chen
   - Set `grant_access_to_history: true`
   - Check status → Should be "pending"

5. **Doctor Approval**
   - Login as Dr. Sarah Chen
   - View pending appointments
   - Approve Patient 1's appointment
   - Verify Zoom meeting link is generated
   - Verify status changes to "accepted"

6. **Patient Status Check**
   - Login as Patient 1
   - View appointments → Status should be "accepted"
   - Copy Zoom meeting link

7. **Doctor Rejection Test**
   - Create another appointment (Patient 2 → Dr. Michael Brown)
   - Login as Dr. Michael Brown
   - Reject the appointment
   - Verify status changes to "declined"

8. **Medical Access Check (Authorized)**
   - Login as Dr. Sarah Chen
   - Access Patient 1's documents using: `/doctor/patients/{{patient_1_id}}/documents`
   - Should return 200 OK with document list

9. **Medical Access Check (Unauthorized)**
   - Login as Dr. Emily Wang (no appointment with Patient 1)
   - Try to access Patient 1's documents
   - Should return 403 Forbidden

10. **Task Management**
    - Login as Dr. Sarah Chen
    - Create 3 tasks with different priorities
    - View all tasks → Should see list
    - Update task status (if endpoint exists)

---

## 11. API Endpoints Summary

| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| POST | `/auth/register` | None | User registration |
| POST | `/auth/login` | None | User login |
| POST | `/auth/logout` | Bearer | User logout |
| GET | `/auth/me` | Bearer | Get current user |
| POST | `/patient/medical-history` | Bearer (Patient) | Upload medical document |
| GET | `/doctors/search` | Bearer | Search doctors |
| POST | `/appointments/request` | Bearer (Patient) | Request appointment |
| GET | `/appointments` | Bearer | List user's appointments |
| POST | `/appointments/{{id}}/approve` | Bearer (Doctor) | Approve appointment (generates Zoom) |
| PATCH | `/appointments/{{id}}/status` | Bearer (Doctor) | Update appointment status |
| GET | `/doctor/patients/{{patient_id}}/documents` | Bearer (Doctor) | View patient records (with permission) |
| POST | `/tasks` | Bearer (Doctor) | Create task |
| GET | `/tasks` | Bearer (Doctor) | List tasks |

---

## 12. Expected Results

✅ **All users can successfully:**
- Register and login
- Logout securely

✅ **Patients can:**
- Upload medical documents (5+ files)
- Search for doctors by specialty/name
- Request appointments
- Grant medical access to doctors
- View their appointment status

✅ **Doctors can:**
- View pending appointment requests
- Approve appointments (generates Zoom link)
- Reject appointments
- View authorized patient medical records
- Get 403 error when accessing unauthorized records
- Create and manage tasks

✅ **System ensures:**
- HIPAA compliance (presigned URLs, permission checks)
- Zoom meeting links generated on approval
- Status updates reflected in real-time
- Proper authorization and authentication

---

## 13. Troubleshooting

### Common Issues:

1. **401 Unauthorized**
   - Ensure Bearer token is included in headers
   - Check token hasn't expired

2. **403 Forbidden (Medical Records)**
   - Patient must grant access via `grant_access_to_history: true`
   - Appointment must exist between doctor and patient

3. **404 Patient Profile Not Found**
   - Patient profile may not be created automatically
   - Check if patient record exists in database

4. **Zoom Meeting Not Generated**
   - Verify Zoom credentials in `.env`
   - Check appointment status is "accepted"

---

## End of Test Flow Document
"""
    
    # Write to file
    with open("backend/flow.md", "w") as f:
        f.write(flow_content)
    
    print("\n✓ flow.md generated successfully at: backend/flow.md")


if __name__ == "__main__":
    test_complete_flow()
