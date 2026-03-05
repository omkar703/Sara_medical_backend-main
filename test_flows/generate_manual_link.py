import requests
import psycopg2
import time
from datetime import datetime, timedelta, timezone

BASE_URL = "http://localhost:8000/api/v1"
DB_CONFIG = {
    "dbname": "saramedico_dev",
    "user": "saramedico_user",
    "password": "SaraMed1c0_Dev_2024!Secure",
    "host": "postgres",
    "port": "5432",
}

DOCTOR_EMAIL   = "doctor.manual.test@saramedico.com"
PATIENT_EMAIL  = "patient.manual.test@example.com"
PASSWORD       = "SecurePass123!"

def clean_db():
    print("\n[DB Cleanup] Removing previous manual test data...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("DELETE FROM audit_logs WHERE user_id IN (SELECT id FROM users WHERE email IN (%s, %s));", (DOCTOR_EMAIL, PATIENT_EMAIL))
        cur.execute("DELETE FROM consultations WHERE doctor_id IN (SELECT id FROM users WHERE email = %s) OR patient_id IN (SELECT id FROM users WHERE email = %s);", (DOCTOR_EMAIL, PATIENT_EMAIL))
        cur.execute("DELETE FROM patients WHERE id IN (SELECT id FROM users WHERE email IN (%s, %s));", (DOCTOR_EMAIL, PATIENT_EMAIL))
        cur.execute("DELETE FROM users WHERE email IN (%s, %s);", (DOCTOR_EMAIL, PATIENT_EMAIL))
        conn.commit()
        cur.close()
        conn.close()
        print("   ✅ DB cleaned.")
    except Exception as e:
        print(f"   ⚠ DB cleanup warning: {e}")

def main():
    clean_db()
    
    # Step 1: Register Doctor
    r = requests.post(f"{BASE_URL}/auth/register", json={
        "email": DOCTOR_EMAIL,
        "password": PASSWORD,
        "first_name": "Manual",
        "last_name": "Doctor",
        "role": "doctor",
        "organization_name": "Manual Test Clinic",
        "phone": "+919000000004",
    })
    
    # Step 2: Login
    r = requests.post(f"{BASE_URL}/auth/login", json={"email": DOCTOR_EMAIL, "password": PASSWORD})
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 3: Onboard Patient
    r = requests.post(f"{BASE_URL}/patients", headers=headers, json={
        "fullName": "Manual Test Patient",
        "email": PATIENT_EMAIL,
        "password": PASSWORD,
        "dateOfBirth": "1990-01-01",
        "gender": "male",
        "phoneNumber": "+919000000005",
        "address": {"street": "2 Test St", "city": "Pune", "state": "MH", "zipCode": "411001"},
        "emergencyContact": {"name": "EC", "relationship": "Friend", "phoneNumber": "+919000000006"},
        "medicalHistory": "None",
        "allergies": [],
        "medications": [],
    })
    patient_id = r.json()["id"]
    
    # Step 4: Schedule
    scheduled_at = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()
    r = requests.post(f"{BASE_URL}/consultations", headers=headers, json={
        "patientId": patient_id,
        "scheduledAt": scheduled_at,
        "durationMinutes": 30,
        "notes": "Manual SOAP test.",
    })
    
    data = r.json()
    print("\n" + "="*60)
    print("  🚀 READY FOR MANUAL TESTING")
    print("="*60)
    print(f"   Doctor Email:   {DOCTOR_EMAIL}")
    print(f"   Doctor Pass:    {PASSWORD}")
    print(f"   Patient Email:  {PATIENT_EMAIL}")
    print(f"   Consultation ID: {data['id']}")
    print(f"\n   🔗 GOOGLE MEET LINK: {data.get('meetLink')}")
    print("="*60)

if __name__ == "__main__":
    main()
