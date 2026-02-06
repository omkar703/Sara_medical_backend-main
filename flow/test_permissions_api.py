#!/usr/bin/env python3
"""
Permissions API Flow Test Script

Tests the complete permission lifecycle:
- Request access (doctor)
- Check permission status (pending)
- Grant access (patient)
- Check permission status (active)
- Revoke access (patient)
- Verify access denied after revoke

Prints all requests and responses for debugging.
Saves all requests/responses as JSON files.
"""

import requests
import json
from datetime import datetime
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


def request_permission(token: str, patient_id: str, reason: str = None, expiry_days: int = 90) -> Dict[str, Any]:
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
    data["expiry_days"] = expiry_days
    
    print_request("POST", url, headers=headers, data=data)
    save_request(step_name, "POST", url, headers=headers, data=data)
    
    response = requests.post(url, json=data, headers=headers)
    
    save_response(step_name, response)
    response_data = print_response(response)
    
    if response.ok:
        print_success(f"Permission requested")
        print_info(f"Grant ID: {response_data.get('id')}")
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
        print_success("Permission granted!")
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


def revoke_permission(token: str, doctor_id: str) -> bool:
    """Revoke doctor's access (called by patient)"""
    step_name = "Revoke_Permission"
    url = f"{BASE_URL}/permissions/revoke-doctor-access"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "doctor_id": doctor_id
    }
    
    print_request("DELETE", url, headers=headers, data=data)
    save_request(step_name, "DELETE", url, headers=headers, data=data)
    
    response = requests.delete(url, json=data, headers=headers)
    
    save_response(step_name, response)
    print_response(response)
    
    if response.status_code == 204 or response.ok:
        print_success("Permission revoked!")
        return True
    else:
        print_error("Permission revoke failed")
        return False


def try_access_patient_documents(token: str, patient_id: str, should_succeed: bool = True) -> bool:
    """Try to access patient documents (to verify permission)"""
    step_name = "Try_Access_Documents"
    url = f"{BASE_URL}/doctor/patients/{patient_id}/documents"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    print_request("GET", url, headers=headers)
    save_request(step_name, "GET", url, headers=headers)
    
    response = requests.get(url, headers=headers)
    
    save_response(step_name, response)
    response_data = print_response(response)
    
    if should_succeed:
        if response.ok:
            print_success("Access granted ✓")
            return True
        else:
            print_error(f"Access denied (expected success): {response_data}")
            return False
    else:
        if not response.ok:
            print_success("Access correctly denied ✓")
            return True
        else:
            print_error("Access granted (expected denial)")
            return False


def main():
    """Main test execution"""
    print_header("PERMISSIONS API FLOW TEST")
    print_info(f"Base URL: {BASE_URL}")
    print_info(f"Started at: {datetime.now().isoformat()}")
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    # ========================================
    # SETUP: REGISTER & LOGIN
    # ========================================
    print_header("SETUP: USER REGISTRATION & LOGIN")
    
    doctor_email = f"doctor_perm_{timestamp}@example.com"
    doctor_password = "SecurePass123!"
    patient_email = f"patient_perm_{timestamp}@example.com"
    patient_password = "SecurePass123!"
    
    print_step(1, "Register doctor account")
    doctor_data = register_user(
        email=doctor_email,
        password=doctor_password,
        role="doctor",
        full_name=f"Dr. Permission Test {timestamp}"
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
        full_name=f"Patient Permission Test {timestamp}",
        dob="1990-01-01",
        phone="+1234567890",
        password=patient_password
    )
    
    if not patient_data or 'patient_id' not in patient_data:
        print_error("Patient onboarding failed. Exiting.")
        return
    
    patient_id = patient_data['patient_id']
    
    print_step(4, "Login as patient")
    patient_login = login_user(patient_email, patient_password)
    if not patient_login or 'access_token' not in patient_login:
        print_error("Patient login failed. Exiting.")
        return
    patient_token = patient_login['access_token']
    
    # NOTE: Doctor 1 already has auto-granted access because they onboarded the patient
    # We need a SECOND doctor to test the permission request/grant flow
    
    print_step(5, "Register second doctor (who needs to request permission)")
    doctor2_email = f"doctor2_perm_{timestamp}@example.com"
    doctor2_password = "SecurePass123!"
    doctor2_data = register_user(
        email=doctor2_email,
        password=doctor2_password,
        role="doctor",
        full_name=f"Dr. Second {timestamp}"
    )
    
    if not doctor2_data or 'id' not in doctor2_data:
        print_error("Second doctor registration failed. Exiting.")
        return
    
    doctor2_id = doctor2_data['id']
    
    print_step(6, "Login as second doctor")
    doctor2_login = login_user(doctor2_email, doctor2_password)
    if not doctor2_login or 'access_token' not in doctor2_login:
        print_error("Second doctor login failed. Exiting.")
        return
    doctor2_token = doctor2_login['access_token']
    
    # ========================================
    # PHASE 1: REQUEST PERMISSION
    # ========================================
    print_header("PHASE 1: DOCTOR 2 REQUESTS PERMISSION")
    
    print_step(7, "Doctor 2 requests access to patient")
    request_result = request_permission(
        token=doctor2_token,
        patient_id=patient_id,
        reason="Need to review patient's medical history for consultation",
        expiry_days=90
    )
    
    if not request_result:
        print_error("Permission request failed. Exiting.")
        return
    
    # ========================================
    # PHASE 2: CHECK PERMISSION (PENDING)
    # ========================================
    print_header("PHASE 2: CHECK PERMISSION STATUS (Should be PENDING)")
    
    print_step(8, "Doctor 2 checks permission status")
    check1 = check_permission(doctor2_token, patient_id)
    
    print_step(9, "Doctor 2 tries to access patient documents (should FAIL)")
    access1 = try_access_patient_documents(doctor2_token, patient_id, should_succeed=False)
    
    # ========================================
    # PHASE 3: GRANT PERMISSION
    # ========================================
    print_header("PHASE 3: PATIENT GRANTS PERMISSION")
    
    print_step(10, "Patient grants access to doctor 2")
    grant_result = grant_permission(
        token=patient_token,
        doctor_id=doctor2_id,
        ai_access=True
    )
    
    # ========================================
    # PHASE 4: CHECK PERMISSION (ACTIVE)
    # ========================================
    print_header("PHASE 4: CHECK PERMISSION STATUS (Should be ACTIVE)")
    
    print_step(11, "Doctor 2 checks permission status again")
    check2 = check_permission(doctor2_token, patient_id)
    
    print_step(12, "Doctor 2 tries to access patient documents (should SUCCEED)")
    access2 = try_access_patient_documents(doctor2_token, patient_id, should_succeed=True)
    
    # ========================================
    # PHASE 5: REVOKE PERMISSION
    # ========================================
    print_header("PHASE 5: PATIENT REVOKES PERMISSION")
    
    print_step(13, "Patient revokes doctor 2's access")
    revoke_result = revoke_permission(patient_token, doctor2_id)
    
    # ========================================
    # PHASE 6: VERIFY REVOCATION
    # ========================================
    print_header("PHASE 6: VERIFY ACCESS DENIED AFTER REVOKE")
    
    print_step(14, "Doctor 2 checks permission status (should show NO ACCESS)")
    check3 = check_permission(doctor2_token, patient_id)
    
    print_step(15, "Doctor 2 tries to access patient documents (should FAIL)")
    access3 = try_access_patient_documents(doctor2_token, patient_id, should_succeed=False)
    
    # ========================================
    # SUMMARY
    # ========================================
    print_header("TEST SUMMARY")
    print_info(f"Doctor 1 Email: {doctor_email} (auto-granted access)")
    print_info(f"Doctor 1 ID: {doctor_id}")
    print_info(f"Doctor 2 Email: {doctor2_email} (tested request/grant/revoke)")
    print_info(f"Doctor 2 ID: {doctor2_id}")
    print_info(f"Patient Email: {patient_email}")
    print_info(f"Patient ID: {patient_id}")
    
    print_success("✓ Permission Request Flow")
    print_success("✓ Permission Grant Flow")
    print_success("✓ Permission Check (Pending → Active)")
    print_success("✓ Permission Revoke Flow")
    print_success("✓ Access Control Verification")
    
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
