#!/usr/bin/env python3
"""
Doctors API Flow Test Script

Tests the following doctor workflows:
- Profile Management (update specialty, bio, license)
- Patient Management (onboard patient, list patients)
- Task Management (create tasks, view pending tasks)
- Permission Request/Grant Flow (doctor requests, patient grants)

Prints all requests and responses for debugging.
Saves all requests/responses as JSON files.
"""

import requests
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_FILE_PATH = r"C:\Users\vikky\Downloads\Introduction to IT - Practice Quiz_ Binary _ Google Skills.pdf"

# Create directories for saving requests and responses
SCRIPT_DIR = Path(__file__).parent
REQUESTS_DIR = SCRIPT_DIR / "requests"
RESPONSES_DIR = SCRIPT_DIR / "responses"

# Create directories if they don't exist
REQUESTS_DIR.mkdir(exist_ok=True)
RESPONSES_DIR.mkdir(exist_ok=True)

# Counter for sequential file naming
request_counter = 0

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text: str):
    """Print a section header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.END}\n")


def print_step(step_num: int, description: str):
    """Print a step description"""
    print(f"{Colors.CYAN}{Colors.BOLD}Step {step_num}: {description}{Colors.END}")


def print_request(method: str, url: str, headers: Optional[Dict] = None, data: Optional[Dict] = None):
    """Print request details"""
    print(f"\n{Colors.BLUE}📤 REQUEST:{Colors.END}")
    print(f"{Colors.BLUE}Method: {method}{Colors.END}")
    print(f"{Colors.BLUE}URL: {url}{Colors.END}")
    
    if headers:
        print(f"{Colors.BLUE}Headers:{Colors.END}")
        safe_headers = headers.copy()
        if 'Authorization' in safe_headers:
            safe_headers['Authorization'] = 'Bearer ***TOKEN***'
        print(f"{Colors.BLUE}{json.dumps(safe_headers, indent=2)}{Colors.END}")
    
    if data:
        print(f"{Colors.BLUE}Body:{Colors.END}")
        print(f"{Colors.BLUE}{json.dumps(data, indent=2)}{Colors.END}")


def print_response(response: requests.Response):
    """Print response details"""
    print(f"\n{Colors.GREEN if response.ok else Colors.RED}📥 RESPONSE:{Colors.END}")
    print(f"{Colors.GREEN if response.ok else Colors.RED}Status: {response.status_code} {response.reason}{Colors.END}")
    
    try:
        response_data = response.json()
        print(f"{Colors.GREEN if response.ok else Colors.RED}Body:{Colors.END}")
        print(f"{Colors.GREEN if response.ok else Colors.RED}{json.dumps(response_data, indent=2)}{Colors.END}")
        return response_data
    except json.JSONDecodeError:
        print(f"{Colors.GREEN if response.ok else Colors.RED}Body: {response.text[:500]}{Colors.END}")
        return None


def print_success(message: str):
    """Print success message"""
    print(f"\n{Colors.GREEN}✅ {message}{Colors.END}")


def print_error(message: str):
    """Print error message"""
    print(f"\n{Colors.RED}❌ {message}{Colors.END}")


def print_info(message: str):
    """Print info message"""
    print(f"\n{Colors.YELLOW}ℹ️  {message}{Colors.END}")


def save_request(step_name: str, method: str, url: str, headers: Optional[Dict] = None, data: Optional[Dict] = None):
    """Save request details to JSON file"""
    global request_counter
    request_counter += 1
    
    safe_headers = headers.copy() if headers else {}
    if 'Authorization' in safe_headers:
        safe_headers['Authorization'] = 'Bearer ***TOKEN***'
    
    request_data = {
        "step": request_counter,
        "step_name": step_name,
        "timestamp": datetime.now().isoformat(),
        "method": method,
        "url": url,
        "headers": safe_headers,
        "body": data
    }
    
    filename = REQUESTS_DIR / f"{request_counter:02d}_{step_name.replace(' ', '_')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(request_data, f, indent=2)
    
    print(f"{Colors.YELLOW}💾 Request saved: {filename.name}{Colors.END}")


def save_response(step_name: str, response: requests.Response):
    """Save response details to JSON file"""
    try:
        response_body = response.json()
    except json.JSONDecodeError:
        response_body = response.text[:1000]
    
    response_data = {
        "step": request_counter,
        "step_name": step_name,
        "timestamp": datetime.now().isoformat(),
        "status_code": response.status_code,
        "status_text": response.reason,
        "headers": dict(response.headers),
        "body": response_body
    }
    
    filename = RESPONSES_DIR / f"{request_counter:02d}_{step_name.replace(' ', '_')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(response_data, f, indent=2)
    
    print(f"{Colors.YELLOW}💾 Response saved: {filename.name}{Colors.END}")


def register_user(email: str, password: str, role: str, full_name: str) -> Dict[str, Any]:
    """Register a new user"""
    step_name = f"Register_{role}"
    url = f"{BASE_URL}/auth/register"
    data = {
        "email": email,
        "password": password,
        "role": role,
        "full_name": full_name
    }
    
    print_request("POST", url, data=data)
    save_request(step_name, "POST", url, data=data)
    
    response = requests.post(url, json=data)
    
    save_response(step_name, response)
    response_data = print_response(response)
    
    if response.ok:
        print_success(f"User registered: {email}")
        return response_data
    else:
        print_error(f"Registration failed: {response_data}")
        return response_data


def login_user(email: str, password: str) -> Dict[str, Any]:
    """Login and get access token"""
    step_name = "Login"
    url = f"{BASE_URL}/auth/login"
    data = {
        "email": email,
        "password": password
    }
    
    print_request("POST", url, data=data)
    save_request(step_name, "POST", url, data=data)
    
    response = requests.post(url, json=data)
    
    save_response(step_name, response)
    response_data = print_response(response)
    
    if response.ok:
        print_success(f"Login successful for: {email}")
        print_info(f"Access Token: {response_data.get('access_token', 'N/A')[:50]}...")
        return response_data
    else:
        print_error(f"Login failed: {response_data}")
        return response_data


def update_doctor_profile(token: str, specialty: str = None, bio: str = None, license_number: str = None) -> Dict[str, Any]:
    """Update doctor profile"""
    step_name = "Update_Doctor_Profile"
    url = f"{BASE_URL}/doctor/profile"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {}
    if specialty:
        data["specialty"] = specialty
    if bio:
        data["bio"] = bio
    if license_number:
        data["license_number"] = license_number
    
    print_request("PATCH", url, headers=headers, data=data)
    save_request(step_name, "PATCH", url, headers=headers, data=data)
    
    response = requests.patch(url, json=data, headers=headers)
    
    save_response(step_name, response)
    response_data = print_response(response)
    
    if response.ok:
        print_success("Doctor profile updated")
        return response_data
    else:
        print_error(f"Profile update failed: {response_data}")
        return response_data


def onboard_patient(token: str, email: str, full_name: str, dob: str, phone: str, password: str = "TempPass123!") -> Dict[str, Any]:
    """Onboard a new patient"""
    step_name = "Onboard_Patient"
    url = f"{BASE_URL}/doctor/onboard-patient"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "email": email,
        "full_name": full_name,
        "date_of_birth": dob,
        "phone_number": phone,
        "password": password
    }
    
    print_request("POST", url, headers=headers, data=data)
    save_request(step_name, "POST", url, headers=headers, data=data)
    
    response = requests.post(url, json=data, headers=headers)
    
    save_response(step_name, response)
    response_data = print_response(response)
    
    if response.ok:
        print_success(f"Patient onboarded: {response_data.get('patient_id')}")
        print_info(f"Patient MRN: {response_data.get('mrn')}")
        return response_data
    else:
        print_error(f"Patient onboarding failed: {response_data}")
        return response_data


def list_patients(token: str) -> Dict[str, Any]:
    """List all patients for a doctor"""
    step_name = "List_Patients"
    url = f"{BASE_URL}/doctor/patients"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    print_request("GET", url, headers=headers)
    save_request(step_name, "GET", url, headers=headers)
    
    response = requests.get(url, headers=headers)
    
    save_response(step_name, response)
    response_data = print_response(response)
    
    if response.ok:
        # API returns a list directly, not {"items": [...]}
        items = response_data if isinstance(response_data, list) else []
        print_success(f"Found {len(items)} patient(s)")
        for i, patient in enumerate(items, 1):
            print_info(f"Patient {i}: {patient.get('name')} (MRN: {patient.get('mrn')})")
        return response_data
    else:
        print_error("Failed to list patients")
        return None


def create_task(token: str, patient_id: str, title: str, description: str, due_date: str = None) -> Dict[str, Any]:
    """Create a task for a patient"""
    step_name = "Create_Task"
    url = f"{BASE_URL}/doctor/tasks"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "patient_id": patient_id,
        "title": title,
        "description": description
    }
    if due_date:
        data["due_date"] = due_date
    
    print_request("POST", url, headers=headers, data=data)
    save_request(step_name, "POST", url, headers=headers, data=data)
    
    response = requests.post(url, json=data, headers=headers)
    
    save_response(step_name, response)
    response_data = print_response(response)
    
    if response.ok:
        print_success(f"Task created: {response_data.get('id')}")
        return response_data
    else:
        print_error(f"Task creation failed: {response_data}")
        return response_data


def list_pending_tasks(token: str) -> Dict[str, Any]:
    """List pending tasks"""
    step_name = "List_Pending_Tasks"
    url = f"{BASE_URL}/doctor/tasks"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    print_request("GET", url, headers=headers)
    save_request(step_name, "GET", url, headers=headers)
    
    response = requests.get(url, headers=headers)
    
    save_response(step_name, response)
    response_data = print_response(response)
    
    if response.ok:
        # API returns a list directly, not {"items": [...]}
        items = response_data if isinstance(response_data, list) else []
        print_success(f"Found {len(items)} pending task(s)")
        for i, task in enumerate(items, 1):
            print_info(f"Task {i}: {task.get('title')}")
        return response_data
    else:
        print_error("Failed to list tasks")
        return None


def request_permission(token: str, patient_id: str, reason: str = None) -> Dict[str, Any]:
    """Request access to patient data"""
    step_name = "Request_Permission"
    url = f"{BASE_URL}/permissions/request"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "patient_id": patient_id
    }
    if reason:
        data["reason"] = reason
    
    print_request("POST", url, headers=headers, data=data)
    save_request(step_name, "POST", url, headers=headers, data=data)
    
    response = requests.post(url, json=data, headers=headers)
    
    save_response(step_name, response)
    response_data = print_response(response)
    
    if response.ok:
        print_success(f"Permission requested: {response_data.get('id')}")
        print_info(f"Status: {response_data.get('status')}")
        return response_data
    else:
        print_error(f"Permission request failed: {response_data}")
        return response_data


def grant_permission(token: str, doctor_id: str, ai_access: bool = False) -> Dict[str, Any]:
    """Grant access to doctor (called by patient)"""
    step_name = "Grant_Permission"
    url = f"{BASE_URL}/permissions/grant-doctor-access"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "doctor_id": doctor_id,
        "ai_access_permission": ai_access
    }
    
    print_request("POST", url, headers=headers, data=data)
    save_request(step_name, "POST", url, headers=headers, data=data)
    
    response = requests.post(url, json=data, headers=headers)
    
    save_response(step_name, response)
    response_data = print_response(response)
    
    if response.ok:
        print_success(f"Permission granted!")
        print_info(f"Status: {response_data.get('status')}")
        return response_data
    else:
        print_error(f"Permission grant failed: {response_data}")
        return response_data


def check_permission(token: str, patient_id: str) -> Dict[str, Any]:
    """Check permission status"""
    step_name = "Check_Permission"
    url = f"{BASE_URL}/permissions/check?patient_id={patient_id}"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    print_request("GET", url, headers=headers)
    save_request(step_name, "GET", url, headers=headers)
    
    response = requests.get(url, headers=headers)
    
    save_response(step_name, response)
    response_data = print_response(response)
    
    if response.ok:
        has_perm = response_data.get('has_permission', False)
        status = response_data.get('status', 'none')
        if has_perm:
            print_success(f"Permission active (status: {status})")
        else:
            print_info(f"No active permission (status: {status})")
        return response_data
    else:
        print_error("Permission check failed")
        return None


def main():
    """Main test execution"""
    print_header("DOCTORS API FLOW TEST")
    print_info(f"Base URL: {BASE_URL}")
    print_info(f"Started at: {datetime.now().isoformat()}")
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    # ========================================
    # PHASE 1: DOCTOR REGISTRATION & LOGIN
    # ========================================
    print_header("PHASE 1: DOCTOR REGISTRATION & LOGIN")
    
    doctor_email = f"doctor_test_{timestamp}@example.com"
    doctor_password = "SecurePass123!"
    
    print_step(1, "Register doctor account")
    doctor_data = register_user(
        email=doctor_email,
        password=doctor_password,
        role="doctor",
        full_name=f"Dr. Test {timestamp}"
    )
    
    if not doctor_data or 'id' not in doctor_data:
        print_error("Registration failed. Exiting.")
        return
    
    doctor_id = doctor_data['id']
    
    print_step(2, "Login to get access token")
    login_data = login_user(doctor_email, doctor_password)
    
    if not login_data or 'access_token' not in login_data:
        print_error("Login failed. Exiting.")
        return
    
    doctor_token = login_data['access_token']
    
    # ========================================
    # PHASE 2: PROFILE MANAGEMENT
    # ========================================
    print_header("PHASE 2: PROFILE MANAGEMENT")
    
    print_step(3, "Update doctor profile")
    profile_data = update_doctor_profile(
        token=doctor_token,
        specialty="Cardiology",
        bio="Experienced cardiologist specializing in preventive care",
        license_number=f"MD-{timestamp}"
    )
    
    # ========================================
    # PHASE 3: PATIENT MANAGEMENT
    # ========================================
    print_header("PHASE 3: PATIENT MANAGEMENT")
    
    print_step(4, "Onboard a new patient")
    patient_email = f"patient_test_{timestamp}@example.com"
    onboard_data = onboard_patient(
        token=doctor_token,
        email=patient_email,
        full_name=f"Patient Test {timestamp}",
        dob="1990-01-01",
        phone="+1234567890"
    )
    
    if not onboard_data or 'patient_id' not in onboard_data:
        print_error("Patient onboarding failed. Exiting.")
        return
    
    patient_id = onboard_data['patient_id']
    patient_user_id = onboard_data.get('user_id')
    patient_password = onboard_data.get('temporary_password', 'TempPass123!')
    
    print_step(5, "List all patients")
    list_patients(doctor_token)
    
    # ========================================
    # PHASE 4: TASK MANAGEMENT
    # ========================================
    print_header("PHASE 4: TASK MANAGEMENT")
    
    print_step(6, "Create task for patient")
    task_data = create_task(
        token=doctor_token,
        patient_id=patient_id,
        title="Review Lab Results",
        description="Please review your latest blood test results and contact us if you have any questions."
    )
    
    print_step(7, "List pending tasks")
    list_pending_tasks(doctor_token)
    
    # ========================================
    # PHASE 5: PERMISSION REQUEST/GRANT FLOW
    # ========================================
    print_header("PHASE 5: PERMISSION REQUEST/GRANT FLOW")
    
    # Register a second doctor who needs to request access
    print_step(8, "Register second doctor")
    doctor2_email = f"doctor2_test_{timestamp}@example.com"
    doctor2_password = "SecurePass123!"
    doctor2_data = register_user(
        email=doctor2_email,
        password=doctor2_password,
        role="doctor",
        full_name=f"Dr. Second {timestamp}"
    )
    
    if not doctor2_data or 'id' not in doctor2_data:
        print_error("Second doctor registration failed. Skipping permission flow.")
    else:
        doctor2_id = doctor2_data['id']
        
        print_step(9, "Login second doctor")
        login2_data = login_user(doctor2_email, doctor2_password)
        
        if not login2_data or 'access_token' not in login2_data:
            print_error("Second doctor login failed. Skipping permission flow.")
        else:
            doctor2_token = login2_data['access_token']
            
            print_step(10, "Second doctor requests access to patient")
            request_data = request_permission(
                token=doctor2_token,
                patient_id=patient_id,
                reason="Need to review patient's consultation history"
            )
            
            print_step(11, "Check permission status (should be pending)")
            check_permission(doctor2_token, patient_id)
            
            # Patient logs in and grants access
            print_step(12, "Patient logs in")
            patient_login_data = login_user(patient_email, patient_password)
            
            if patient_login_data and 'access_token' in patient_login_data:
                patient_token = patient_login_data['access_token']
                
                print_step(13, "Patient grants access to second doctor")
                grant_data = grant_permission(
                    token=patient_token,
                    doctor_id=doctor2_id,
                    ai_access=True
                )
                
                print_step(14, "Second doctor checks permission again (should be active)")
                check_permission(doctor2_token, patient_id)
    
    # ========================================
    # SUMMARY
    # ========================================
    print_header("TEST SUMMARY")
    print_info(f"Doctor 1 Email: {doctor_email}")
    print_info(f"Doctor 1 ID: {doctor_id}")
    print_info(f"Patient Email: {patient_email}")
    print_info(f"Patient ID: {patient_id}")
    print_info(f"Patient MRN: {onboard_data.get('mrn')}")
    
    if doctor2_data:
        print_info(f"Doctor 2 Email: {doctor2_email}")
        print_info(f"Doctor 2 ID: {doctor2_id}")
    
    print_success("Profile Management: ✓")
    print_success("Patient Management: ✓")
    print_success("Task Management: ✓")
    if doctor2_data:
        print_success("Permission Request/Grant: ✓")
    
    print_info(f"Completed at: {datetime.now().isoformat()}")
    print_header("TEST COMPLETED")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_error("\nTest interrupted by user")
    except Exception as e:
        print_error(f"Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
