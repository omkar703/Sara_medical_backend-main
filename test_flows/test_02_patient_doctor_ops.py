import requests
import uuid

BASE_URL = "http://localhost:8000/api/v1"

def test_patient_doctor_operations():
    print("="*60)
    print("🧪 STARTING: Patient & Doctor Operations Flow Test")
    print("="*60)

    unique_id = str(uuid.uuid4())[:8]
    doctor_email = f"dr_smith_{unique_id}@saramedico.com"
    patient_email = f"patient_john_{unique_id}@saramedico.com"
    password = "SecurePass123!"

    # ---------------------------------------------------------
    # 1. Register and Login Doctor
    # ---------------------------------------------------------
    print(f"\n[1] Registering and Logging in Doctor: {doctor_email}")
    requests.post(f"{BASE_URL}/auth/register", json={
        "email": doctor_email,
        "password": password,
        "full_name": "Dr. Smith Test",
        "role": "doctor",
        "organization_name": "Saramedico General"
    })
    
    doc_login = requests.post(f"{BASE_URL}/auth/login", json={"email": doctor_email, "password": password})
    if doc_login.status_code != 200:
        print(f"   ❌ FAILED: Doctor login. {doc_login.text}")
        return
        
    doc_token = doc_login.json().get("access_token")
    doc_headers = {"Authorization": f"Bearer {doc_token}"}
    print("   ✅ SUCCESS: Doctor authenticated.")

    # ---------------------------------------------------------
    # 2. Update Doctor Profile (PATCH /doctor/profile)
    # ---------------------------------------------------------
    print("\n[2] Updating Doctor Profile (Adding Specialty)...")
    profile_payload = {
        "specialty": "Neurology",
        "license_number": f"LIC-{unique_id}"
    }
    profile_res = requests.patch(f"{BASE_URL}/doctor/profile", headers=doc_headers, json=profile_payload)
    
    if profile_res.status_code == 200:
        print("   ✅ SUCCESS: Doctor profile updated to Neurology.")
    else:
        print(f"   ❌ FAILED: Profile update returned {profile_res.status_code}. {profile_res.text}")

    # ---------------------------------------------------------
    # 3. Doctor Onboards a Patient (POST /patients)
    # ---------------------------------------------------------
    print(f"\n[3] Doctor onboarding new patient: {patient_email}")
    # Using alias fields matching the Pydantic schema
    patient_payload = {
        "fullName": "John Doe",
        "email": patient_email,
        "password": password,
        "dateOfBirth": "1985-05-15",
        "gender": "male",
        "phoneNumber": "+12345678900"
    }
    
    onboard_res = requests.post(f"{BASE_URL}/patients", headers=doc_headers, json=patient_payload)
    
    if onboard_res.status_code == 201:
        patient_data = onboard_res.json()
        patient_id = patient_data.get('id')
        print(f"   ✅ SUCCESS: Patient onboarded. Assigned MRN: {patient_data.get('mrn')}")
    else:
        print(f"   ❌ FAILED: Patient onboarding returned {onboard_res.status_code}. {onboard_res.text}")
        return

    # ---------------------------------------------------------
    # 4. Patient Login Verification (POST /auth/login)
    # ---------------------------------------------------------
    print("\n[4] Verifying Patient can log in with onboarded credentials...")
    pat_login = requests.post(f"{BASE_URL}/auth/login", json={"email": patient_email, "password": password})
    
    if pat_login.status_code == 200:
        pat_token = pat_login.json().get("access_token")
        pat_headers = {"Authorization": f"Bearer {pat_token}"}
        print("   ✅ SUCCESS: Patient authenticated successfully.")
    else:
        print(f"   ❌ FAILED: Patient login returned {pat_login.status_code}. {pat_login.text}")
        return

    # ---------------------------------------------------------
    # 5. Doctor views Patient Directory (GET /doctor/patients)
    # ---------------------------------------------------------
    print("\n[5] Doctor retrieving their patient directory...")
    doc_patients_res = requests.get(f"{BASE_URL}/doctor/patients", headers=doc_headers)
    
    if doc_patients_res.status_code == 200:
        patients_list = doc_patients_res.json()
        print(f"   ✅ SUCCESS: Doctor fetched {len(patients_list)} patient(s).")
        if len(patients_list) > 0:
            print(f"   First Patient Name: {patients_list[0].get('name')}")
    else:
        print(f"   ❌ FAILED: Fetching patients returned {doc_patients_res.status_code}. {doc_patients_res.text}")

    # ---------------------------------------------------------
    # 6. Patient Searches for Doctor (GET /doctors/search)
    # ---------------------------------------------------------
    print("\n[6] Patient searching for 'Neurology' doctors...")
    search_res = requests.get(f"{BASE_URL}/doctors/search?specialty=Neurology", headers=pat_headers)
    
    if search_res.status_code == 200:
        search_results = search_res.json().get("results", [])
        print(f"   ✅ SUCCESS: Search returned {len(search_results)} doctor(s).")
        # Ensure our newly created doctor is in the results
        if any(doc.get("name") == "Dr. Smith Test" for doc in search_results):
            print("   ✅ SUCCESS: Onboarding Doctor successfully appeared in search results.")
        else:
            print("   ⚠️ WARNING: Doctor not found in search results.")
    else:
        print(f"   ❌ FAILED: Search returned {search_res.status_code}. {search_res.text}")

    print("\n" + "="*60)
    print("🏁 Patient & Doctor Operations Flow Test Complete")
    print("="*60)

if __name__ == "__main__":
    test_patient_doctor_operations()