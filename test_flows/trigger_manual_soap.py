import requests
import time

BASE_URL = "http://localhost:8000/api/v1"
DOCTOR_EMAIL = "doctor.manual.test@saramedico.com"
PASSWORD = "SecurePass123!"
CONSULTATION_ID = "a6225833-e1e2-431c-a197-473b5689db84"

def main():
    # 1. Login
    print(f"Logging in as {DOCTOR_EMAIL}...")
    r = requests.post(f"{BASE_URL}/auth/login", json={"email": DOCTOR_EMAIL, "password": PASSWORD})
    if r.status_code != 200:
        print(f"Login failed: {r.text}")
        return
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Complete Consultation
    print(f"Completing consultation {CONSULTATION_ID}...")
    r = requests.post(f"{BASE_URL}/consultations/{CONSULTATION_ID}/complete", headers=headers)
    if r.status_code != 200:
        print(f"Complete failed: {r.text}")
        return
    print("✅ Consultation marked as completed. AI generation started.")

    # 3. Poll for SOAP Note
    soap_url = f"{BASE_URL}/consultations/{CONSULTATION_ID}/soap-note"
    print("\nPolling for AI SOAP Note (this can take 2-4 minutes for Google Meet to process)...")
    for i in range(40):
        time.sleep(10)
        r = requests.get(soap_url, headers=headers)
        if r.status_code == 200:
            print("\n" + "✨" * 20)
            print("  AI SOAP NOTE GENERATED!")
            print("✨" * 20)
            soap_data = r.json()
            note = soap_data.get("soap_note", {})
            print(f"\n[SUBJECTIVE]\n{note.get('subjective')}")
            print(f"\n[OBJECTIVE]\n{note.get('objective')}")
            print(f"\n[ASSESSMENT]\n{note.get('assessment')}")
            print(f"\n[PLAN]\n{note.get('plan')}")
            return
        elif r.status_code == 202:
            print(f"Attempt {i+1}: Still processing...")
        else:
            print(f"Attempt {i+1}: Status {r.status_code} - {r.text}")

    print("\n❌ Timed out waiting for SOAP note.")

if __name__ == "__main__":
    main()
