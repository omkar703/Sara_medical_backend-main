import requests
import uuid

BASE_URL = "http://localhost:8000/api/v1"

def test_permissions_flow():
    print("="*60)
    print("🧪 STARTING: Permission-Based Access Control Flow Test")
    print("="*60)

    unique_id = str(uuid.uuid4())[:8]
    doctor_email = f"dr_perm_{unique_id}@saramedico.com"
    patient_email = f"patient_perm_{unique_id}@saramedico.com"
    password = "SecurePass123!"

    # ---------------------------------------------------------
    # Setup: Create Doctor and Patient, and get tokens
    # ---------------------------------------------------------
    print("\n[Setup] Creating Doctor and Patient accounts...")
    
    # 1. Register Doctor
    requests.post(f"{BASE_URL}/auth/register", json={
        "email": doctor_email, "password": password, 
        "full_name": "Dr. Permissions", "role": "doctor"
    })
    
    # Login Doctor
    doc_login = requests.post(f"{BASE_URL}/auth/login", json={"email": doctor_email, "password": password}).json()
    doc_token = doc_login.get("access_token")
    doc_id = doc_login.get("user", {}).get("id")
    doc_headers = {"Authorization": f"Bearer {doc_token}"}

    # 2. Doctor onboards Patient
    pat_res = requests.post(f"{BASE_URL}/patients", headers=doc_headers, json={
        "fullName": "Permissions Patient", "email": patient_email, 
        "password": password, "dateOfBirth": "1990-01-01"
    })
    
    # Login Patient
    pat_login = requests.post(f"{BASE_URL}/auth/login", json={"email": patient_email, "password": password}).json()
    pat_token = pat_login.get("access_token")
    pat_id = pat_login.get("user", {}).get("id")
    pat_headers = {"Authorization": f"Bearer {pat_token}"}

    print("   ✅ Setup Complete: Doctor and Patient created and authenticated.")

    # ---------------------------------------------------------
    # 1. Check Initial State (Should NOT have access)
    # Note: Onboarding does NOT automatically grant DataAccessGrant 
    # unless specifically coded. Let's verify.
    # ---------------------------------------------------------
    print("\n[1] Doctor checking permission state (Initial)...")
    check_res = requests.get(f"{BASE_URL}/permissions/check?patient_id={pat_id}", headers=doc_headers)
    
    # The system might grant access on creation, or it might not. 
    # Let's assume the strict flow where it needs explicit grant.
    if check_res.status_code == 200:
        has_perm = check_res.json().get("has_permission")
        print(f"   Status: Doctor currently {'HAS' if has_perm else 'DOES NOT HAVE'} permission.")
    else:
        print(f"   ❌ FAILED: Check permission returned {check_res.status_code}. {check_res.text}")
        return

    # ---------------------------------------------------------
    # 2. Patient Grants Access to Doctor (POST /permissions/grant-doctor-access)
    # ---------------------------------------------------------
    print("\n[2] Patient granting explicit access to Doctor...")
    grant_payload = {
        "doctor_id": doc_id,
        "ai_access_permission": True,
        "access_level": "read_analyze",
        "expiry_days": 30,
        "reason": "Test Grant"
    }
    
    grant_res = requests.post(f"{BASE_URL}/permissions/grant-doctor-access", headers=pat_headers, json=grant_payload)
    
    if grant_res.status_code == 201:
        print("   ✅ SUCCESS: Access granted.")
    else:
        print(f"   ❌ FAILED: Grant access returned {grant_res.status_code}. {grant_res.text}")
        return

    # ---------------------------------------------------------
    # 3. Verify Doctor Has Access (GET /permissions/check)
    # ---------------------------------------------------------
    print("\n[3] Doctor verifying access was granted...")
    verify_res = requests.get(f"{BASE_URL}/permissions/check?patient_id={pat_id}", headers=doc_headers)
    
    if verify_res.status_code == 200 and verify_res.json().get("has_permission") is True:
        print("   ✅ SUCCESS: System confirms Doctor now has access.")
    else:
        print(f"   ❌ FAILED: Verification returned {verify_res.status_code} or permission is false. {verify_res.text}")

    # ---------------------------------------------------------
    # 4. Patient Revokes Access (DELETE /permissions/revoke-doctor-access)
    # ---------------------------------------------------------
    print("\n[4] Patient revoking access from Doctor...")
    revoke_payload = {
        "doctor_id": doc_id
    }
    
    revoke_res = requests.delete(f"{BASE_URL}/permissions/revoke-doctor-access", headers=pat_headers, json=revoke_payload)
    
    if revoke_res.status_code == 200:
        print("   ✅ SUCCESS: Access revoked.")
    else:
        print(f"   ❌ FAILED: Revoke access returned {revoke_res.status_code}. {revoke_res.text}")
        return

    # ---------------------------------------------------------
    # 5. Verify Doctor Lost Access (GET /permissions/check)
    # ---------------------------------------------------------
    print("\n[5] Doctor verifying access was removed...")
    final_check_res = requests.get(f"{BASE_URL}/permissions/check?patient_id={pat_id}", headers=doc_headers)
    
    if final_check_res.status_code == 200 and final_check_res.json().get("has_permission") is False:
        print("   ✅ SUCCESS: System confirms Doctor no longer has access.")
    else:
        print(f"   ❌ FAILED: Final verification returned {final_check_res.status_code} or permission is true. {final_check_res.text}")

    print("\n" + "="*60)
    print("🏁 Permission-Based Access Control Flow Test Complete")
    print("="*60)

if __name__ == "__main__":
    test_permissions_flow()