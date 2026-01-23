import httpx
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/v1"

def test_phase6_workflow():
    # 1. Login as Doctor
    print("\n--- 1. Login as Doctor ---")
    login_data = {"email": "doctor_e2e_final@test.com", "password": "Password123"}
    resp = httpx.post(f"{BASE_URL}/auth/login", json=login_data)
    if resp.status_code != 200:
        print(f"Doctor login failed: {resp.text}")
        return
    doctor_token = resp.json()["access_token"]
    doctor_headers = {"Authorization": f"Bearer {doctor_token}"}
    doctor_id = resp.json()["user"]["id"]
    print("Doctor Authenticated.")

    # 2. Update Specialty
    print("\n--- 2. PATCH /doctor/profile (Set Specialty) ---")
    profile_data = {"specialty": "Cardiology", "license_number": "LIC-12345-CARD"}
    resp = httpx.patch(f"{BASE_URL}/doctor/profile", json=profile_data, headers=doctor_headers)
    print(f"Status: {resp.status_code}")
    print(resp.json())

    # 3. Login as Patient
    print("\n--- 3. Login as Patient ---")
    login_data = {"email": "patient_e2e_final@test.com", "password": "Password123"}
    resp = httpx.post(f"{BASE_URL}/auth/login", json=login_data)
    if resp.status_code != 200:
        print(f"Patient login failed: {resp.text}")
        return
    patient_token = resp.json()["access_token"]
    patient_headers = {"Authorization": f"Bearer {patient_token}"}
    print("Patient Authenticated.")

    # 4. Search Doctors by Specialty
    print("\n--- 4. GET /doctors/search?specialty=Cardiology ---")
    resp = httpx.get(f"{BASE_URL}/doctors/search?specialty=Cardiology", headers=patient_headers)
    print(f"Status: {resp.status_code}")
    results = resp.json()["results"]
    print(f"Found {len(results)} doctors.")
    for d in results:
        print(f"- {d['name']} ({d['specialty']})")

    # 5. Request Appointment
    print("\n--- 5. POST /appointments/request ---")
    # Request for 1 week from now
    target_date = (datetime.utcnow() + timedelta(days=7)).isoformat()
    req_data = {
        "doctor_id": doctor_id,
        "requested_date": target_date,
        "reason": "Chest pain"
    }
    resp = httpx.post(f"{BASE_URL}/appointments/request", json=req_data, headers=patient_headers)
    print(f"Status: {resp.status_code}")
    appointment = resp.json()
    appointment_id = appointment["id"]
    print(f"Appointment Requested. ID: {appointment_id}")

    # 6. Approve Appointment (Zoom Integration)
    print("\n--- 6. POST /appointments/{id}/approve (Generate Zoom) ---")
    # Confirmed for precisely 1 week from now
    confirm_date = (datetime.utcnow() + timedelta(days=7, hours=1)).isoformat()
    approve_data = {
        "appointment_time": confirm_date,
        "doctor_notes": "Please bring your previous reports."
    }
    resp = httpx.post(f"{BASE_URL}/appointments/{appointment_id}/approve", json=approve_data, headers=doctor_headers)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        final_app = resp.json()
        print("Zoom Links Generated:")
        print(f"- Join URL (Patient): {final_app.get('join_url')}")
        print(f"- Start URL (Doctor): {final_app.get('start_url')}")
        print(f"- Meeting ID: {final_app.get('meeting_id')}")
    else:
        print(f"Approval failed: {resp.text}")

    # 7. Check Activity Feed
    print("\n--- 7. GET /doctor/activity ---")
    resp = httpx.get(f"{BASE_URL}/doctor/activity", headers=doctor_headers)
    if resp.status_code == 200:
        print("Latest Activity:")
        print(json.dumps(resp.json()[0], indent=2))

if __name__ == "__main__":
    test_phase6_workflow()
