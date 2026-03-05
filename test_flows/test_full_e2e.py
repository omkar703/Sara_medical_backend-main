"""
End-to-End Test: Full Consultation + AI SOAP Note Flow
=====================================================
Run this from the PROJECT ROOT (host machine):
    python3 test_flows/test_full_e2e.py

Steps:
    1. Register a new doctor
    2. Login and get token
    3. Onboard a new patient (with real email for calendar invite)
    4. Schedule a consultation → produces Google Meet link
    5. Complete the consultation → triggers AI SOAP note generation
    6. Poll for and print the AI SOAP note
"""

import requests
import psycopg2
import time
from datetime import datetime, timedelta, timezone

BASE_URL = "http://localhost:8000/api/v1"

# DB config for pre-test cleanup (matches docker-compose.yml)
DB_CONFIG = {
    "dbname": "saramedico_dev",
    "user": "saramedico_user",
    "password": "SaraMed1c0_Dev_2024!Secure",
    "host": "localhost",
    "port": "5435",
}

# ─── Test credentials ────────────────────────────────────────────────────────
DOCTOR_EMAIL   = "doctor.e2e.test@saramedico.com"
PATIENT_EMAIL  = "patient.e2e.test@example.com"  # Must be a real email to get calendar invite
PASSWORD       = "SecurePass123!"


def step(n: int, title: str):
    print(f"\n{'─'*60}")
    print(f"  Step {n}: {title}")
    print(f"{'─'*60}")


def clean_db():
    """Remove any leftover test accounts so the test is idempotent."""
    print("\n[DB Cleanup] Removing previous test data...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        # Must delete in correct FK order: audit_logs → consultations → patients → users
        cur.execute("""
            DELETE FROM audit_logs
            WHERE user_id IN (SELECT id FROM users WHERE email IN (%s, %s));
        """, (DOCTOR_EMAIL, PATIENT_EMAIL))
        cur.execute("""
            DELETE FROM consultations
            WHERE doctor_id IN (SELECT id FROM users WHERE email = %s)
               OR patient_id IN (SELECT id FROM users WHERE email = %s);
        """, (DOCTOR_EMAIL, PATIENT_EMAIL))
        cur.execute("""
            DELETE FROM patients WHERE id IN (
                SELECT id FROM users WHERE email IN (%s, %s)
            );
        """, (DOCTOR_EMAIL, PATIENT_EMAIL))
        cur.execute("DELETE FROM users WHERE email IN (%s, %s);", (DOCTOR_EMAIL, PATIENT_EMAIL))
        conn.commit()
        cur.close()
        conn.close()
        print("   ✅ DB cleaned.")
    except Exception as e:
        print(f"   ⚠ DB cleanup warning (safe to ignore): {e}")



def main():
    print("\n" + "="*60)
    print("  🧪  E2E CONSULTATION + AI SOAP NOTE TEST")
    print("="*60)

    clean_db()

    # ── Step 1: Register Doctor ───────────────────────────────────────────────
    step(1, "Register Doctor")
    r = requests.post(f"{BASE_URL}/auth/register", json={
        "email": DOCTOR_EMAIL,
        "password": PASSWORD,
        "first_name": "E2E",
        "last_name": "Doctor",
        "role": "doctor",
        "organization_name": "E2E Test Clinic",
        "phone": "+919000000001",
    })
    if r.status_code not in (200, 201):
        print(f"   ❌ Register failed ({r.status_code}): {r.text}")
        return
    print(f"   ✅ Doctor registered: {DOCTOR_EMAIL}")

    # ── Step 2: Login ─────────────────────────────────────────────────────────
    step(2, "Login as Doctor")
    r = requests.post(f"{BASE_URL}/auth/login", json={"email": DOCTOR_EMAIL, "password": PASSWORD})
    if r.status_code != 200:
        print(f"   ❌ Login failed ({r.status_code}): {r.text}")
        return
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"   ✅ Login successful. Token acquired.")

    # ── Step 3: Onboard Patient ───────────────────────────────────────────────
    step(3, "Onboard Patient")
    r = requests.post(f"{BASE_URL}/patients", headers=headers, json={
        "fullName": "E2E Test Patient",
        "email": PATIENT_EMAIL,
        "password": PASSWORD,
        "dateOfBirth": "1992-05-15",
        "gender": "female",
        "phoneNumber": "+919000000002",
        "address": {
            "street": "1 Test Street",
            "city": "Pune",
            "state": "Maharashtra",
            "zipCode": "411001",
        },
        "emergencyContact": {
            "name": "Emergency Contact",
            "relationship": "Spouse",
            "phoneNumber": "+919000000003",
        },
        "medicalHistory": "None significant.",
        "allergies": ["Penicillin"],
        "medications": [],
    })
    if r.status_code not in (200, 201):
        print(f"   ❌ Patient onboard failed ({r.status_code}): {r.text}")
        return
    patient_id = r.json()["id"]
    print(f"   ✅ Patient onboarded. ID: {patient_id}")
    print(f"      (Calendar invite will be sent to: {PATIENT_EMAIL})")

    # ── Step 4: Schedule Consultation → Creates Google Meet ───────────────────
    step(4, "Schedule Consultation (Create Google Meet)")
    scheduled_at = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()
    r = requests.post(f"{BASE_URL}/consultations", headers=headers, json={
        "patientId": patient_id,
        "scheduledAt": scheduled_at,
        "durationMinutes": 30,
        "notes": "E2E automated test consultation.",
    })
    if r.status_code != 200:
        print(f"   ❌ Schedule failed ({r.status_code}): {r.text}")
        return
    data = r.json()
    consultation_id = data["id"]
    meet_link = data.get("meetLink")
    print(f"   ✅ Consultation scheduled! ID: {consultation_id}")
    print(f"   🔗 Google Meet Link: {meet_link}")
    print(f"   📅 Calendar Event ID: {data.get('googleEventId')}")
    print(f"\n   👉 Both doctor ({DOCTOR_EMAIL}) and patient ({PATIENT_EMAIL})")
    print(f"      should have received Calendar invites with this meeting link.")
    print(f"\n   ⏳ Simulating meeting... (in real usage, open the Meet link, talk, then complete)")

    # ── Step 5: Complete Consultation → Triggers AI ───────────────────────────
    step(5, "Complete Consultation (Trigger AI SOAP Note)")
    r = requests.post(f"{BASE_URL}/consultations/{consultation_id}/complete", headers=headers)
    if r.status_code != 200:
        print(f"   ❌ Complete failed ({r.status_code}): {r.text}")
        return
    result = r.json()
    print(f"   ✅ {result['message']}")
    print(f"   🤖 AI Status: {result['ai_status']}")
    print(f"   📋 Poll URL: {result['soap_note_url']}")

    # ── Step 6: Poll for SOAP Note ────────────────────────────────────────────
    step(6, "Polling for AI SOAP Note (up to 4 mins)")
    soap_url = f"{BASE_URL}/consultations/{consultation_id}/soap-note"
    for attempt in range(40):
        time.sleep(10)
        r = requests.get(soap_url, headers=headers)
        if r.status_code == 200:
            print(f"\n   🌟  AI SOAP NOTE GENERATED SUCCESSFULLY! 🌟\n")
            soap_data = r.json()
            soap_note = soap_data.get("soap_note", {})
            print(f"   {'─'*56}")
            print(f"   SUBJECTIVE:\n   {soap_note.get('subjective', 'N/A')}\n")
            print(f"   OBJECTIVE:\n   {soap_note.get('objective', 'N/A')}\n")
            print(f"   ASSESSMENT:\n   {soap_note.get('assessment', 'N/A')}\n")
            print(f"   PLAN:\n   {soap_note.get('plan', 'N/A')}")
            print(f"   {'─'*56}")
            print(f"\n   ✅ ALL STEPS PASSED. The full flow works end-to-end!\n")
            return
        elif r.status_code == 202:
            print(f"   [{attempt+1}/40] Still processing... (Waiting on Google Meet & AI)")
        else:
            print(f"   [{attempt+1}/40] Status {r.status_code}: {r.text[:80]}")

    print("\n   ❌ SOAP note generation timed out after 4 minutes.")
    print("      Check Celery worker logs: docker logs saramedico_celery_worker --tail 50")


if __name__ == "__main__":
    main()
