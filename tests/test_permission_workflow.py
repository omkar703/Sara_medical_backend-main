
import asyncio
import httpx
from datetime import datetime
import json
import sys
import os

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
OUTPUT_FILE = "permission_test_output.txt"

async def run_test():
    async with httpx.AsyncClient(timeout=30.0) as client:
        log("=== STARTING PERMISSION WORKFLOW TEST ===\n")

        # 1. Setup: Register Doctor A, Doctor B, and Patient
        log("--- Step 1: User Registration ---")
        
        # Register Doctor A (Creator)
        doc_a_email = f"doc_a_{datetime.now().timestamp()}@test.com"
        doc_a = await register_user(client, doc_a_email, "doctor", "Doctor A")
        
        # Register Doctor B (Requester)
        doc_b_email = f"doc_b_{datetime.now().timestamp()}@test.com"
        doc_b = await register_user(client, doc_b_email, "doctor", "Doctor B")
        
        # Register Patient (Onboarded by Doctor A)
        log("Onboarding patient via Doctor A...")
        try:
            onboard_resp = await client.post(
                f"{BASE_URL}/doctor/onboard-patient",
                headers={"Authorization": f"Bearer {doc_a['access_token']}"},
                json={
                    "email": f"patient_{datetime.now().timestamp()}@test.com",
                    "password": "Password123!",
                    "full_name": "Test Patient",
                    "phone_number": "+1234567890",
                    "date_of_birth": "1990-01-01",
                    "gender": "male"
                }
            )
            if onboard_resp.status_code == 200:
                patient_data = onboard_resp.json()
                log(f"Patient Onboarded: {patient_data.get('email', 'unknown')}")
                
                 # Login directly
                login_resp = await client.post(f"{BASE_URL}/auth/login", json={
                    "email": patient_data["email"],
                    "password": "Password123!"
                })
                
                if login_resp.status_code == 200:
                    patient = login_resp.json()
                    log(f"Patient Logged In: {patient['user']['id']}")
                else:
                    log(f"Patient Login Failed: {login_resp.text}")
                    return
            else:
                log(f"Onboarding Failed: {onboard_resp.text}")
                return
        except Exception as e:
            log(f"Onboarding Exception: {e}")
            return
        
        log(f"Users created:\nDoc A: {doc_a['user']['id']}\nDoc B: {doc_b['user']['id']}\nPatient: {patient['user']['id']}\n")

        # 2. Doctor B requests access (Should be Pending)
        log("--- Step 2: Doctor B Requests Access ---")
        try:
            resp = await client.post(
                f"{BASE_URL}/permissions/request",
                headers={"Authorization": f"Bearer {doc_b['access_token']}"},
                json={"patient_id": patient['user']['id'], "reason": "Second opinion"}
            )
            log(f"Request Response: {resp.status_code} - {resp.json()}")
        except Exception as e:
            log(f"Request Failed: {e}")

        # 3. Check Status (Should NOT have access yet)
        log("\n--- Step 3: Verify No Access Yet ---")
        check_resp = await client.get(
            f"{BASE_URL}/permissions/check",
            headers={"Authorization": f"Bearer {doc_b['access_token']}"},
            params={"patient_id": patient['user']['id']}
        )
        log(f"Permission Check (Before Grant): {check_resp.json()}")

        # 4. Patient Grants Access (Approves Request)
        log("\n--- Step 4: Patient Grants Access ---")
        grant_resp = await client.post(
            f"{BASE_URL}/permissions/grant-doctor-access",
            headers={"Authorization": f"Bearer {patient['access_token']}"},
            json={
                "doctor_id": doc_b['user']['id'],
                "ai_access_permission": True,
                "access_level": "read_analyze",
                "expiry_days": 30,
                "reason": "Approved for second opinion"
            }
        )
        log(f"Grant Response: {grant_resp.status_code} - {grant_resp.json()}")

        # 5. Check Status (Should HAVE access now)
        log("\n--- Step 5: Verify Active Access ---")
        check_resp_after = await client.get(
            f"{BASE_URL}/permissions/check",
            headers={"Authorization": f"Bearer {doc_b['access_token']}"},
            params={"patient_id": patient['user']['id']}
        )
        log(f"Permission Check (After Grant): {check_resp_after.json()}")

        # 6. Revoke Access
        log("\n--- Step 6: Patient Revokes Access ---")
        revoke_resp = await client.request(
            "DELETE",
            f"{BASE_URL}/permissions/revoke-doctor-access",
            headers={"Authorization": f"Bearer {patient['access_token']}"},
            json={"doctor_id": doc_b['user']['id']}
        )
        log(f"Revoke Response: {revoke_resp.status_code} - {revoke_resp.json()}")

        # 7. Final Check
        log("\n--- Step 7: Verify Revoked Access ---")
        final_check = await client.get(
            f"{BASE_URL}/permissions/check",
            headers={"Authorization": f"Bearer {doc_b['access_token']}"},
            params={"patient_id": patient['user']['id']}
        )
        log(f"Permission Check (Final): {final_check.json()}")
        
        log("\n=== TEST COMPLETE ===")

def log(message):
    print(message)
    with open(OUTPUT_FILE, "a") as f:
        f.write(message + "\n")

async def register_user(client, email, role, name):
    resp = await client.post(f"{BASE_URL}/auth/register", json={
        "email": email,
        "password": "Password123!",
        "full_name": name,
        "role": role
    })
    
    if resp.status_code == 201 or resp.status_code == 200:
        # Login to get token
        login_resp = await client.post(f"{BASE_URL}/auth/login", json={
            "email": email,
            "password": "Password123!"
        })
        return login_resp.json()
    else:
        log(f"Failed to register {email}: {resp.text}")
        return None

if __name__ == "__main__":
    # Clear previous output
    open(OUTPUT_FILE, 'w').close()
    try:
        asyncio.run(run_test())
        print(f"\nResults saved to {OUTPUT_FILE}")
    except Exception as e:
        print(f"Test Execution Failed: {e}")
