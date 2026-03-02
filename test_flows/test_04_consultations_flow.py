import requests
import psycopg2
from datetime import datetime, timedelta, timezone

BASE_URL = "http://localhost:8000/api/v1"

# Database credentials based on your docker-compose.yml
DB_CONFIG = {
    "dbname": "saramedico_dev",
    "user": "saramedico_user",
    "password": "SaraMed1c0_Dev_2024!Secure",
    "host": "localhost",
    "port": "5435"
}

def clean_database(emails):
    print("\n[Database Cleanup] Removing existing test emails...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Because of foreign key constraints, we might need to delete from child tables first 
        # if ON DELETE CASCADE is not fully configured everywhere. 
        # Let's delete by email.
        for email in emails:
            # Delete from users (this should cascade to patients, appointments, consultations)
            cur.execute("DELETE FROM users WHERE email = %s;", (email,))
            
        conn.commit()
        cur.close()
        conn.close()
        print(f"   ✅ SUCCESS: Cleaned up database for {emails}")
    except Exception as e:
        print(f"   ⚠️ WARNING: Database cleanup failed (maybe tables are locked or missing). Error: {e}")
        print("   Proceeding anyway...")


def test_consultations_flow():
    print("="*60)
    print("🧪 STARTING: Consultations & Google Meet Flow Test")
    print("="*60)

    # Using the real emails
    doctor_email = "nikhilhegde1011@gmail.com"
    patient_email = "hegdenikhil101@gmail.com"
    password = "SecurePass123!"

    # 0. Clean the DB first
    clean_database([doctor_email, patient_email])

    # ---------------------------------------------------------
    # Setup: Create Doctor and Patient, and get tokens
    # ---------------------------------------------------------
    print("\n[Setup] Creating accounts...")
    
    # 1. Register/Login Doctor
    print(f"   -> Registering Doctor: {doctor_email}")
    requests.post(f"{BASE_URL}/auth/register", json={
        "email": doctor_email, "password": password, 
        "full_name": "Dr. Nikhil Hegde", "role": "doctor"
    })
    
    doc_login = requests.post(f"{BASE_URL}/auth/login", json={"email": doctor_email, "password": password})
    if doc_login.status_code != 200:
        print(f"   ❌ FAILED: Doctor login. {doc_login.text}")
        return
        
    doc_token = doc_login.json().get("access_token")
    doc_id = doc_login.json().get("user", {}).get("id")
    doc_headers = {"Authorization": f"Bearer {doc_token}"}

    # 2. Doctor onboards Patient
    print(f"   -> Onboarding Patient: {patient_email}")
    pat_res = requests.post(f"{BASE_URL}/patients", headers=doc_headers, json={
        "fullName": "Patient Nikhil", "email": patient_email, 
        "password": password, "dateOfBirth": "1990-01-01"
    })
    
    pat_login = requests.post(f"{BASE_URL}/auth/login", json={"email": patient_email, "password": password})
    if pat_login.status_code != 200:
        print(f"   ❌ FAILED: Patient login. {pat_login.text}")
        return
        
    pat_id = pat_login.json().get("user", {}).get("id")
    print("   ✅ Setup Complete.")

    # ---------------------------------------------------------
    # 1. Doctor Schedules a Consultation (Triggers Google Meet)
    # ---------------------------------------------------------
    print("\n[1] Doctor scheduling a consultation (Generating Real Google Meet Link)...")
    # Schedule for 2 hours from now
    consultation_time = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
    print(consultation_time)
    
    consult_payload = {
        "patientId": pat_id,
        "scheduledAt": consultation_time,
        "durationMinutes": 30,
        "notes": "Initial Telehealth Consultation."
    }
    
    consult_res = requests.post(f"{BASE_URL}/consultations", headers=doc_headers, json=consult_payload)
    
    if consult_res.status_code == 200:
        consult_data = consult_res.json()
        print(f"   ✅ SUCCESS: Consultation scheduled!")
        print(f"   📅 Google Event ID: {consult_data.get('google_event_id')}")
        print(f"   🔗 Google Meet Link: {consult_data.get('meet_link')}")
        print("   👉 Check your email inboxes for the Calendar Invites!")
    else:
        print(f"   ❌ FAILED: Consultation scheduling returned {consult_res.status_code}. {consult_res.text}")
        return

    # ---------------------------------------------------------
    # 2. Doctor Lists their Consultations
    # ---------------------------------------------------------
    print("\n[2] Doctor retrieving their consultation list...")
    list_res = requests.get(f"{BASE_URL}/consultations?status=scheduled", headers=doc_headers)
    
    if list_res.status_code == 200:
        consult_list = list_res.json().get("consultations", [])
        print(f"   ✅ SUCCESS: Doctor sees {len(consult_list)} scheduled consultation(s).")
    else:
        print(f"   ❌ FAILED: Fetching consultations returned {list_res.status_code}. {list_res.text}")

    print("\n" + "="*60)
    print("🏁 Consultations & Google Meet Flow Test Complete")
    print("="*60)

if __name__ == "__main__":
    test_consultations_flow()