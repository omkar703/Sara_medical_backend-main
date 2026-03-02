import requests
import uuid
from datetime import datetime

# Base URL for the Saramedico API
BASE_URL = "http://localhost:8000/api/v1"

def test_doctor_patient_flow():
    print("="*50)
    print("🧪 STARTING: Doctor-Patient Flow Test")
    print("="*50)

    # 1. Register a Doctor
    doctor_uuid = str(uuid.uuid4())[:8]
    doctor_email = f"test_doctor_{doctor_uuid}@saramedico.com"
    password = "SecurePass123!"

    print(f"\n[1] Registering new doctor: {doctor_email}")
    reg_payload = {
        "email": doctor_email,
        "password": password,
        "full_name": f"Dr. Test {doctor_uuid}",
        "role": "doctor",
        "organization_name": "Test Hospital"
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=reg_payload)
    
    # Check if we get a redirect or created status
    if response.status_code in [201, 303]:
        print("   ✅ SUCCESS: Doctor registered.")
    else:
        print(f"   ❌ FAILED: Doctor registration returned {response.status_code}")
        print(f"   Details: {response.text}")
        return

    # 2. Login as Doctor to get Token
    print("\n[2] Logging in as Doctor to get JWT Tokens...")
    login_payload = {
        "email": doctor_email,
        "password": password
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_payload)
    
    if response.status_code == 200:
        tokens = response.json()
        access_token = tokens.get("access_token")
        print("   ✅ SUCCESS: Doctor login successful. Access token acquired.")
    else:
        print(f"   ❌ FAILED: Doctor login returned {response.status_code}")
        print(f"   Details: {response.text}")
        return

    # 3. Add a Patient (Doctor onboarding patient)
    patient_uuid = str(uuid.uuid4())[:8]
    patient_email = f"test_patient_{patient_uuid}@saramedico.com"
    
    print(f"\n[3] Doctor onboarding new patient: {patient_email}")
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    patient_payload = {
        "fullName": f"Test Patient {patient_uuid}",
        "email": patient_email,
        "password": "SecurePass123!",
        "dateOfBirth": "1990-01-01",
        "gender": "other",
        "phoneNumber": "+12345678900"
    }
    
    response = requests.post(f"{BASE_URL}/patients", headers=headers, json=patient_payload)
    
    if response.status_code == 201:
        patient_data = response.json()
        print("   ✅ SUCCESS: Patient onboarded by Doctor.")
        print(f"   Patient MRN: {patient_data.get('mrn')}")
    else:
        print(f"   ❌ FAILED: Patient onboarding returned {response.status_code}")
        print(f"   Details: {response.text}")
        return

    # 4. Patient Login
    print("\n[4] Logging in as Patient...")
    patient_login_payload = {
        "email": patient_email,
        "password": "SecurePass123!"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=patient_login_payload)
    
    if response.status_code == 200:
        patient_tokens = response.json()
        patient_access_token = patient_tokens.get("access_token")
        print("   ✅ SUCCESS: Patient login successful. Access token acquired.")
    else:
        print(f"   ❌ FAILED: Patient login returned {response.status_code}")
        print(f"   Details: {response.text}")
        return

    # 5. Doctor views their patients
    print("\n[5] Doctor viewing their patient list...")
    response = requests.get(f"{BASE_URL}/doctor/patients", headers=headers)
    
    if response.status_code == 200:
        patients = response.json()
        print(f"   ✅ SUCCESS: Doctor fetched patient list. Count: {len(patients)}")
    else:
        print(f"   ❌ FAILED: Doctor fetching patients returned {response.status_code}")
        print(f"   Details: {response.text}")
        return

    print("\n" + "="*50)
    print("🏁 Doctor-Patient Flow Test Complete")
    print("="*50)

if __name__ == "__main__":
    test_doctor_patient_flow()