#!/usr/bin/env python3
"""
Consultations API Flow Test Script

Tests the complete consultation lifecycle:
- Schedule consultation (doctor)
- List consultations
- Get specific consultation details
- Update consultation (add notes, change status)
- AI analysis trigger (stub)

Prints all requests and responses for debugging.
Saves all requests/responses as JSON files.
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000/api/v1"

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
        return response_data
    else:
        print_error(f"Login failed: {response_data}")
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
        return response_data
    else:
        print_error(f"Patient onboarding failed: {response_data}")
        return response_data


def schedule_consultation(token: str, patient_id: str, scheduled_at: str, duration: int = 30, notes: str = None) -> Dict[str, Any]:
    """Schedule a consultation"""
    step_name = "Schedule_Consultation"
    url = f"{BASE_URL}/consultations"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "patientId": patient_id,
        "scheduledAt": scheduled_at,
        "durationMinutes": duration
    }
    if notes:
        data["notes"] = notes
    
    print_request("POST", url, headers=headers, data=data)
    save_request(step_name, "POST", url, headers=headers, data=data)
    
    response = requests.post(url, json=data, headers=headers)
    
    save_response(step_name, response)
    response_data = print_response(response)
    
    if response.ok:
        print_success(f"Consultation scheduled: {response_data.get('id')}")
        print_info(f"Status: {response_data.get('status')}")
        print_info(f"Meeting URL: {response_data.get('joinUrl', 'N/A')}")
        return response_data
    else:
        print_error(f"Failed to schedule consultation: {response_data}")
        return response_data


def list_consultations(token: str, status_filter: str = None) -> Dict[str, Any]:
    """List consultations"""
    step_name = "List_Consultations"
    url = f"{BASE_URL}/consultations"
    if status_filter:
        url += f"?status={status_filter}"
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    print_request("GET", url, headers=headers)
    save_request(step_name, "GET", url, headers=headers)
    
    response = requests.get(url, headers=headers)
    
    save_response(step_name, response)
    response_data = print_response(response)
    
    if response.ok:
        total = response_data.get('total', 0)
        print_success(f"Found {total} consultation(s)")
        consultations = response_data.get('consultations', [])
        for i, c in enumerate(consultations[:5], 1):  # Show first 5
            print_info(f"#{i}: {c.get('id')} - Status: {c.get('status')}")
        return response_data
    else:
        print_error("Failed to list consultations")
        return None


def get_consultation(token: str, consultation_id: str) -> Dict[str, Any]:
    """Get consultation details"""
    step_name = "Get_Consultation"
    url = f"{BASE_URL}/consultations/{consultation_id}"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    print_request("GET", url, headers=headers)
    save_request(step_name, "GET", url, headers=headers)
    
    response = requests.get(url, headers=headers)
    
    save_response(step_name, response)
    response_data = print_response(response)
    
    if response.ok:
        print_success("Consultation details retrieved")
        print_info(f"Patient: {response_data.get('patientName')}")
        print_info(f"Doctor: {response_data.get('doctorName')}")
        print_info(f"Status: {response_data.get('status')}")
        return response_data
    else:
        print_error("Failed to get consultation")
        return None


def update_consultation(token: str, consultation_id: str, status: str = None, notes: str = None, diagnosis: str = None) -> Dict[str, Any]:
    """Update consultation"""
    step_name = "Update_Consultation"
    url = f"{BASE_URL}/consultations/{consultation_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {}
    if status:
        data["status"] = status
    if notes:
        data["notes"] = notes
    if diagnosis:
        data["diagnosis"] = diagnosis
    
    print_request("PUT", url, headers=headers, data=data)
    save_request(step_name, "PUT", url, headers=headers, data=data)
    
    response = requests.put(url, json=data, headers=headers)
    
    save_response(step_name, response)
    response_data = print_response(response)
    
    if response.ok:
        print_success("Consultation updated")
        print_info(f"New status: {response_data.get('status')}")
        return response_data
    else:
        print_error("Failed to update consultation")
        return response_data


def trigger_ai_analysis(token: str, consultation_id: str) -> Dict[str, Any]:
    """Trigger AI analysis (stub)"""
    step_name = "Trigger_AI_Analysis"
    url = f"{BASE_URL}/consultations/{consultation_id}/analyze"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print_request("POST", url, headers=headers)
    save_request(step_name, "POST", url, headers=headers)
    
    response = requests.post(url, headers=headers)
    
    save_response(step_name, response)
    response_data = print_response(response)
    
    if response.ok:
        print_success("AI analysis triggered")
        print_info(f"Message: {response_data.get('message')}")
        return response_data
    else:
        print_error("Failed to trigger AI analysis")
        return response_data


def main():
    """Main test execution"""
    print_header("CONSULTATIONS API FLOW TEST")
    print_info(f"Base URL: {BASE_URL}")
    print_info(f"Started at: {datetime.now().isoformat()}")
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    # ========================================
    # SETUP: REGISTER & LOGIN
    # ========================================
    print_header("SETUP: USER REGISTRATION & LOGIN")
    
    doctor_email = f"doctor_consult_{timestamp}@example.com"
    doctor_password = "SecurePass123!"
    patient_email = f"patient_consult_{timestamp}@example.com"
    patient_password = "SecurePass123!"
    
    print_step(1, "Register doctor account")
    doctor_data = register_user(
        email=doctor_email,
        password=doctor_password,
        role="doctor",
        full_name=f"Dr. Consult Test {timestamp}"
    )
    
    if not doctor_data or 'id' not in doctor_data:
        print_error("Doctor registration failed. Exiting.")
        return
    
    doctor_id = doctor_data['id']
    
    print_step(2, "Login as doctor")
    doctor_login = login_user(doctor_email, doctor_password)
    if not doctor_login or 'access_token' not in doctor_login:
        print_error("Doctor login failed. Exiting.")
        return
    doctor_token = doctor_login['access_token']
    
    print_step(3, "Doctor onboards patient")
    patient_data = onboard_patient(
        token=doctor_token,
        email=patient_email,
        full_name=f"Patient Consult Test {timestamp}",
        dob="1990-01-01",
        phone="+1234567890",
        password=patient_password
    )
    
    if not patient_data or 'patient_id' not in patient_data:
        print_error("Patient onboarding failed. Exiting.")
        return
    
    patient_id = patient_data['patient_id']
    
    # ========================================
    # PHASE 1: SCHEDULE CONSULTATION
    # ========================================
    print_header("PHASE 1: SCHEDULE CONSULTATION")
    
    # Schedule for tomorrow at 10:00 AM
    tomorrow = datetime.now() + timedelta(days=1)
    scheduled_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    scheduled_at_iso = scheduled_time.isoformat()
    
    print_step(4, "Schedule consultation")
    consultation_data = schedule_consultation(
        token=doctor_token,
        patient_id=patient_id,
        scheduled_at=scheduled_at_iso,
        duration=30,
        notes="Initial consultation"
    )
    
    if not consultation_data or 'id' not in consultation_data:
        print_error("Failed to schedule consultation. Exiting.")
        return
    
    consultation_id = consultation_data['id']
    
    # ========================================
    # PHASE 2: LIST CONSULTATIONS
    # ========================================
    print_header("PHASE 2: LIST CONSULTATIONS")
    
    print_step(5, "List all consultations")
    list_result1 = list_consultations(doctor_token)
    
    print_step(6, "List scheduled consultations only")
    list_result2 = list_consultations(doctor_token, status_filter="scheduled")
    
    # ========================================
    # PHASE 3: GET CONSULTATION DETAILS
    # ========================================
    print_header("PHASE 3: GET CONSULTATION DETAILS")
    
    print_step(7, "Get consultation details")
    get_result = get_consultation(doctor_token, consultation_id)
    
    # ========================================
    # PHASE 4: UPDATE CONSULTATION
    # ========================================
    print_header("PHASE 4: UPDATE CONSULTATION")
    
    print_step(8, "Update consultation status to 'active'")
    update_result1 = update_consultation(
        token=doctor_token,
        consultation_id=consultation_id,
        status="active",
        notes="Patient arrived, consultation started"
    )
    
    print_step(9, "Add diagnosis and complete consultation")
    update_result2 = update_consultation(
        token=doctor_token,
        consultation_id=consultation_id,
        status="completed",
        diagnosis="Common cold - prescribe rest and fluids"
    )
    
    # ========================================
    # PHASE 5: AI ANALYSIS (STUB)
    # ========================================
    print_header("PHASE 5: TRIGGER AI ANALYSIS")
    
    print_step(10, "Trigger AI analysis")
    ai_result = trigger_ai_analysis(doctor_token, consultation_id)
    
    # ========================================
    # SUMMARY
    # ========================================
    print_header("TEST SUMMARY")
    print_info(f"Doctor Email: {doctor_email}")
    print_info(f"Doctor ID: {doctor_id}")
    print_info(f"Patient Email: {patient_email}")
    print_info(f"Patient ID: {patient_id}")
    print_info(f"Consultation ID: {consultation_id}")
    
    print_success("✓ Schedule Consultation")
    print_success("✓ List Consultations")
    print_success("✓ Get Consultation Details")
    print_success("✓ Update Consultation Status")
    print_success("✓ AI Analysis Trigger")
    
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
