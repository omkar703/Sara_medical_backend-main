#!/usr/bin/env python3
"""
Documents API Flow Test Script

Tests both document upload flows:
- Flow A: Presigned URL (upload-url → MinIO upload → confirm)
- Flow B: Direct Upload (single multipart request)

Prints all requests and responses for debugging.
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
        # Mask sensitive headers
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
    
    # Mask sensitive data
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


def create_patient(token: str) -> Dict[str, Any]:
    """Create a new patient"""
    step_name = "Create_Patient"
    url = f"{BASE_URL}/patients"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "fullName": "John Doe Test",
        "dateOfBirth": "1985-05-15",
        "phone": "+1234567890"
    }
    
    print_request("POST", url, headers=headers, data=data)
    save_request(step_name, "POST", url, headers=headers, data=data)
    
    response = requests.post(url, json=data, headers=headers)
    
    save_response(step_name, response)
    response_data = print_response(response)
    
    if response.ok:
        print_success(f"Patient created with ID: {response_data.get('id')}")
        print_info(f"MRN: {response_data.get('mrn')}")
        return response_data
    else:
        print_error(f"Patient creation failed: {response_data}")
        return response_data


def test_flow_a_presigned_url(token: str, patient_id: str, file_path: str):
    """Test Flow A: Presigned URL upload"""
    print_header("FLOW A: PRESIGNED URL UPLOAD (3-STEP PROCESS)")
    
    # Get file info
    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    file_type = "application/pdf"
    
    print_info(f"File: {file_name}")
    print_info(f"Size: {file_size} bytes")
    print_info(f"Type: {file_type}")
    
    # Step 1: Request upload URL
    print_step(1, "Request presigned upload URL")
    url = f"{BASE_URL}/documents/upload-url"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "fileName": file_name,
        "fileType": file_type,
        "fileSize": file_size,
        "patientId": patient_id
    }
    
    print_request("POST", url, headers=headers, data=data)
    save_request("FlowA_Request_Upload_URL", "POST", url, headers=headers, data=data)
    
    response = requests.post(url, json=data, headers=headers)
    
    save_response("FlowA_Request_Upload_URL", response)
    upload_data = print_response(response)
    
    if not response.ok:
        print_error("Failed to get upload URL")
        return
    
    upload_url = upload_data.get('uploadUrl')
    document_id = upload_data.get('documentId')
    
    print_success(f"Upload URL received")
    print_info(f"Document ID: {document_id}")
    print_info(f"Upload URL: {upload_url[:100]}...")
    
    # Step 2: Upload file to MinIO
    print_step(2, "Upload file to MinIO storage")
    
    with open(file_path, 'rb') as f:
        file_content = f.read()
    
    upload_headers = {
        "Content-Type": file_type
    }
    
    print_request("PUT", upload_url[:100] + "...", headers=upload_headers)
    save_request("FlowA_Upload_To_MinIO", "PUT", upload_url[:100] + "...", headers=upload_headers, data={"note": "Binary file upload"})
    print_info(f"Uploading {len(file_content)} bytes...")
    
    response = requests.put(upload_url, data=file_content, headers=upload_headers)
    
    save_response("FlowA_Upload_To_MinIO", response)
    print_response(response)
    
    if not response.ok:
        print_error("File upload to MinIO failed")
        return
    
    print_success("File uploaded to MinIO successfully")
    
    # Step 3: Confirm upload
    print_step(3, "Confirm document upload")
    url = f"{BASE_URL}/documents/{document_id}/confirm"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "metadata": {
            "category": "test_document",
            "upload_flow": "presigned_url"
        }
    }
    
    print_request("POST", url, headers=headers, data=data)
    save_request("FlowA_Confirm_Upload", "POST", url, headers=headers, data=data)
    
    response = requests.post(url, json=data, headers=headers)
    
    save_response("FlowA_Confirm_Upload", response)
    confirm_data = print_response(response)
    
    if response.ok:
        print_success(f"Document confirmed! ID: {confirm_data.get('id')}")
        print_info(f"File Name: {confirm_data.get('fileName')}")
        print_info(f"Uploaded At: {confirm_data.get('uploadedAt')}")
        return confirm_data
    else:
        print_error("Document confirmation failed")
        return None


def test_flow_b_direct_upload(token: str, patient_id: str, file_path: str):
    """Test Flow B: Direct multipart upload"""
    print_header("FLOW B: DIRECT UPLOAD (1-STEP PROCESS)")
    
    # Get file info
    file_name = os.path.basename(file_path)
    
    print_info(f"File: {file_name}")
    
    # Single step: Direct upload
    print_step(1, "Direct multipart file upload")
    url = f"{BASE_URL}/documents/upload"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # Prepare multipart data
    with open(file_path, 'rb') as f:
        files = {
            'file': (file_name, f, 'application/pdf')
        }
        data = {
            'patient_id': patient_id,
            'notes': 'Test upload via direct flow (Flow B)'
        }
        
        print_request("POST", url, headers=headers)
        save_request("FlowB_Direct_Upload", "POST", url, headers=headers, data={"patient_id": patient_id, "notes": data['notes'], "file": file_name})
        print_info(f"Multipart Form Data:")
        print_info(f"  - file: {file_name}")
        print_info(f"  - patient_id: {patient_id}")
        print_info(f"  - notes: {data['notes']}")
        
        response = requests.post(url, files=files, data=data, headers=headers)
    
    save_response("FlowB_Direct_Upload", response)
    response_data = print_response(response)
    
    if response.ok:
        print_success(f"Document uploaded! ID: {response_data.get('id')}")
        print_info(f"File Name: {response_data.get('fileName')}")
        print_info(f"Uploaded At: {response_data.get('uploadedAt')}")
        return response_data
    else:
        print_error("Direct upload failed")
        return None


def list_documents(token: str, patient_id: str):
    """List all documents for a patient"""
    print_header("LISTING ALL DOCUMENTS")
    
    url = f"{BASE_URL}/documents?patient_id={patient_id}"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    print_request("GET", url, headers=headers)
    save_request("List_Documents", "GET", url, headers=headers)
    
    response = requests.get(url, headers=headers)
    
    save_response("List_Documents", response)
    response_data = print_response(response)
    
    if response.ok:
        items = response_data.get('items', [])
        print_success(f"Found {len(items)} document(s)")
        for i, doc in enumerate(items, 1):
            print_info(f"Document {i}:")
            print(f"    ID: {doc.get('id')}")
            print(f"    Name: {doc.get('fileName')}")
            print(f"    Size: {doc.get('fileSize')} bytes")
            print(f"    Uploaded: {doc.get('uploadedAt')}")
        return response_data
    else:
        print_error("Failed to list documents")
        return None


def main():
    """Main test execution"""
    print_header("DOCUMENTS API FLOW TEST")
    print_info(f"Base URL: {BASE_URL}")
    print_info(f"Test File: {TEST_FILE_PATH}")
    print_info(f"Started at: {datetime.now().isoformat()}")
    
    # Check if file exists
    if not os.path.exists(TEST_FILE_PATH):
        print_error(f"Test file not found: {TEST_FILE_PATH}")
        return
    
    print_success(f"Test file found: {os.path.getsize(TEST_FILE_PATH)} bytes")
    
    # Generate unique email for this test run
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    doctor_email = f"doctor_test_{timestamp}@example.com"
    doctor_password = "SecurePass123!"
    
    # Phase 1: Register Doctor
    print_header("PHASE 1: DOCTOR REGISTRATION")
    print_step(1, "Register doctor account")
    doctor_data = register_user(
        email=doctor_email,
        password=doctor_password,
        role="doctor",
        full_name=f"Dr. Test User {timestamp}"
    )
    
    if not doctor_data or 'id' not in doctor_data:
        print_error("Registration failed. Exiting.")
        return
    
    doctor_id = doctor_data['id']
    
    # Phase 2: Login
    print_header("PHASE 2: DOCTOR LOGIN")
    print_step(2, "Login to get access token")
    login_data = login_user(doctor_email, doctor_password)
    
    if not login_data or 'access_token' not in login_data:
        print_error("Login failed. Exiting.")
        return
    
    access_token = login_data['access_token']
    
    # Phase 3: Create Patient
    print_header("PHASE 3: PATIENT CREATION")
    print_step(3, "Create a new patient")
    patient_data = create_patient(access_token)
    
    if not patient_data or 'id' not in patient_data:
        print_error("Patient creation failed. Exiting.")
        return
    
    patient_id = patient_data['id']
    
    # Phase 4: Test Flow A (Presigned URL)
    # flow_a_result = test_flow_a_presigned_url(access_token, patient_id, TEST_FILE_PATH)
    
    # Phase 5: Test Flow B (Direct Upload)
    flow_b_result = test_flow_b_direct_upload(access_token, patient_id, TEST_FILE_PATH)
    
    # Phase 6: List all documents
    list_documents(access_token, patient_id)
    
    # Summary
    print_header("TEST SUMMARY")
    print_info(f"Doctor Email: {doctor_email}")
    print_info(f"Doctor ID: {doctor_id}")
    print_info(f"Patient ID: {patient_id}")
    print_info(f"Patient MRN: {patient_data.get('mrn')}")

    if flow_b_result:
        print_success(f"Flow B (Direct Upload): Document ID {flow_b_result.get('id')}")
    else:
        print_error("Flow B (Direct Upload): FAILED")
    
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
