import requests
import psycopg2

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
    print("\n[Database Cleanup] Removing existing test users...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        for email in emails:
            cur.execute("DELETE FROM users WHERE email = %s;", (email,))
        conn.commit()
        cur.close()
        conn.close()
        print(f"   ✅ SUCCESS: Cleaned up database for {emails}")
    except Exception as e:
        print(f"   ⚠️ WARNING: Database cleanup failed. Error: {e}")

def test_audit_compliance_flow():
    print("="*60)
    print("🧪 STARTING: Audit & Compliance Flow Test")
    print("="*60)

    admin_email = "audit_admin@saramedico.com"
    doctor_email = "compliance_doctor@saramedico.com"
    password = "SecurePass123!"

    # 0. Clean the DB first
    clean_database([admin_email, doctor_email])

    # ---------------------------------------------------------
    # Setup: Register Admin and Doctor
    # ---------------------------------------------------------
    print("\n[Setup] Registering accounts...")
    
    # Register & Login Admin
    requests.post(f"{BASE_URL}/auth/register", json={
        "email": admin_email, "password": password, 
        "full_name": "Compliance Officer", "role": "admin",
        "organization_name": "Saramedico Central"
    })
    admin_login = requests.post(f"{BASE_URL}/auth/login", json={"email": admin_email, "password": password}).json()
    admin_token = admin_login.get("access_token")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Register & Login Doctor
    requests.post(f"{BASE_URL}/auth/register", json={
        "email": doctor_email, "password": password, 
        "full_name": "Dr. Privacy", "role": "doctor"
    })
    doc_login = requests.post(f"{BASE_URL}/auth/login", json={"email": doctor_email, "password": password}).json()
    doc_token = doc_login.get("access_token")
    doc_headers = {"Authorization": f"Bearer {doc_token}"}

    print("   ✅ Setup Complete.")

    # ---------------------------------------------------------
    # 1. User Requests GDPR Data Export (GET /compliance/my-data)
    # ---------------------------------------------------------
    print("\n[1] Doctor requesting GDPR data export...")
    data_res = requests.get(f"{BASE_URL}/compliance/my-data", headers=doc_headers)
    
    if data_res.status_code == 200:
        exported_data = data_res.json()
        print("   ✅ SUCCESS: User data exported successfully.")
        print(f"   Included sections: {list(exported_data.keys())}")
    else:
        print(f"   ❌ FAILED: Data export returned {data_res.status_code}. {data_res.text}")

    # ---------------------------------------------------------
    # 2. Admin Views Audit Logs (GET /audit/logs)
    # ---------------------------------------------------------
    print("\n[2] Admin fetching recent audit logs...")
    # This should include the doctor's recent login and data export actions
    logs_res = requests.get(f"{BASE_URL}/audit/logs?limit=5", headers=admin_headers)
    
    if logs_res.status_code == 200:
        logs_data = logs_res.json()
        print(f"   ✅ SUCCESS: Admin fetched {logs_data.get('total')} audit logs.")
        if logs_data.get("logs"):
            print(f"   Most recent action: '{logs_data['logs'][0].get('action')}'")
    else:
        print(f"   ❌ FAILED: Audit logs returned {logs_res.status_code}. {logs_res.text}")

    # ---------------------------------------------------------
    # 3. Admin Views Compliance Stats (GET /audit/stats)
    # ---------------------------------------------------------
    print("\n[3] Admin fetching compliance dashboard stats...")
    stats_res = requests.get(f"{BASE_URL}/audit/stats", headers=admin_headers)
    
    if stats_res.status_code == 200:
        print("   ✅ SUCCESS: Compliance stats fetched.")
    else:
        print(f"   ❌ FAILED: Compliance stats returned {stats_res.status_code}. {stats_res.text}")

    # ---------------------------------------------------------
    # 4. Admin Exports Audit Logs CSV (GET /audit/export)
    # ---------------------------------------------------------
    print("\n[4] Admin exporting audit logs as CSV...")
    csv_res = requests.get(f"{BASE_URL}/audit/export", headers=admin_headers)
    
    if csv_res.status_code == 200 and "text/csv" in csv_res.headers.get("Content-Type", ""):
        print("   ✅ SUCCESS: Audit logs successfully exported as CSV.")
    else:
        print(f"   ❌ FAILED: CSV export returned {csv_res.status_code}. {csv_res.text}")

    # ---------------------------------------------------------
    # 5. User Requests Account Deletion (DELETE /compliance/my-account)
    # ---------------------------------------------------------
    print("\n[5] Doctor requesting Account Deletion (Right to be Forgotten)...")
    del_res = requests.delete(f"{BASE_URL}/compliance/my-account", headers=doc_headers)
    
    if del_res.status_code == 200:
        print(f"   ✅ SUCCESS: Account scheduled for deletion: {del_res.json().get('message')}")
    else:
        print(f"   ❌ FAILED: Account deletion returned {del_res.status_code}. {del_res.text}")
        return

    # ---------------------------------------------------------
    # 6. Verify Deletion (Attempt Login)
    # ---------------------------------------------------------
    print("\n[6] Verifying user can no longer log in...")
    check_login = requests.post(f"{BASE_URL}/auth/login", json={"email": doctor_email, "password": password})
    if check_login.status_code in [400, 401, 403, 404]:
        print("   ✅ SUCCESS: Doctor login rejected. Account successfully disabled/deleted.")
    else:
        print(f"   ❌ FAILED: Doctor was able to log in after deletion! Status: {check_login.status_code}")

    print("\n" + "="*60)
    print("🏁 Audit & Compliance Flow Test Complete")
    print("="*60)

if __name__ == "__main__":
    test_audit_compliance_flow()