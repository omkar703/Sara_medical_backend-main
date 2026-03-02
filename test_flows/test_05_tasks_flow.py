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

def clean_database(email):
    print("\n[Database Cleanup] Removing existing test email...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE email = %s;", (email,))
        conn.commit()
        cur.close()
        conn.close()
        print(f"   ✅ SUCCESS: Cleaned up database for {email}")
    except Exception as e:
        print(f"   ⚠️ WARNING: Database cleanup failed. Error: {e}")


def test_tasks_flow():
    print("="*60)
    print("🧪 STARTING: Doctor Tasks & Dashboard Flow Test")
    print("="*60)

    doctor_email = "dr_task_tester@saramedico.com"
    password = "SecurePass123!"

    # 0. Clean the DB first
    clean_database(doctor_email)

    # ---------------------------------------------------------
    # Setup: Create Doctor and get token
    # ---------------------------------------------------------
    print("\n[Setup] Registering and authenticating Doctor...")
    requests.post(f"{BASE_URL}/auth/register", json={
        "email": doctor_email, "password": password, 
        "full_name": "Dr. Task Manager", "role": "doctor"
    })
    
    doc_login = requests.post(f"{BASE_URL}/auth/login", json={"email": doctor_email, "password": password})
    if doc_login.status_code != 200:
        print(f"   ❌ FAILED: Doctor login. {doc_login.text}")
        return
        
    doc_token = doc_login.json().get("access_token")
    doc_headers = {"Authorization": f"Bearer {doc_token}"}
    print("   ✅ Setup Complete.")

    # ---------------------------------------------------------
    # 1. Create a Normal Task (POST /doctor/tasks)
    # ---------------------------------------------------------
    print("\n[1] Creating a 'Normal' priority task...")
    tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    
    normal_task_payload = {
        "title": "Review Patient Labs",
        "description": "Check John Doe's blood work results.",
        "due_date": tomorrow,
        "priority": "normal",
        "status": "pending"
    }
    
    res_normal = requests.post(f"{BASE_URL}/doctor/tasks", headers=doc_headers, json=normal_task_payload)
    if res_normal.status_code == 201:
        normal_task_id = res_normal.json().get("id")
        print(f"   ✅ SUCCESS: Normal task created. ID: {normal_task_id}")
    else:
        print(f"   ❌ FAILED: Task creation returned {res_normal.status_code}. {res_normal.text}")
        return

    # ---------------------------------------------------------
    # 2. Create an Urgent Task (POST /doctor/tasks)
    # ---------------------------------------------------------
    print("\n[2] Creating an 'Urgent' priority task...")
    urgent_task_payload = {
        "title": "Sign Discharge Papers",
        "description": "Patient waiting in room 4.",
        "due_date": tomorrow,
        "priority": "urgent",
        "status": "pending"
    }
    
    res_urgent = requests.post(f"{BASE_URL}/doctor/tasks", headers=doc_headers, json=urgent_task_payload)
    if res_urgent.status_code == 201:
        urgent_task_id = res_urgent.json().get("id")
        print(f"   ✅ SUCCESS: Urgent task created. ID: {urgent_task_id}")
    else:
        print(f"   ❌ FAILED: Task creation returned {res_urgent.status_code}. {res_urgent.text}")

    # ---------------------------------------------------------
    # 3. Retrieve Tasks and Check Sorting (GET /doctor/tasks)
    # ---------------------------------------------------------
    print("\n[3] Fetching task list (Testing sorting logic)...")
    res_list = requests.get(f"{BASE_URL}/doctor/tasks", headers=doc_headers)
    
    if res_list.status_code == 200:
        tasks = res_list.json()
        print(f"   ✅ SUCCESS: Retrieved {len(tasks)} tasks.")
        if len(tasks) > 0:
            # The backend is programmed to sort 'urgent' tasks first
            print(f"   Top Task Title: '{tasks[0].get('title')}' (Priority: {tasks[0].get('priority')})")
            if tasks[0].get("priority") == "urgent":
                print("   ✅ SUCCESS: Urgent task properly sorted to the top!")
            else:
                print("   ⚠️ WARNING: Urgent task is not at the top of the list.")
    else:
        print(f"   ❌ FAILED: Fetching tasks returned {res_list.status_code}. {res_list.text}")

    # ---------------------------------------------------------
    # 4. Update Task Status (PATCH /doctor/tasks/{task_id})
    # ---------------------------------------------------------
    print(f"\n[4] Updating the Normal task status to 'completed'...")
    update_payload = {"status": "completed"}
    
    res_update = requests.patch(f"{BASE_URL}/doctor/tasks/{normal_task_id}", headers=doc_headers, json=update_payload)
    if res_update.status_code == 200:
        print(f"   ✅ SUCCESS: Task status changed to '{res_update.json().get('status')}'.")
    else:
        print(f"   ❌ FAILED: Task update returned {res_update.status_code}. {res_update.text}")

    # ---------------------------------------------------------
    # 5. Delete a Task (DELETE /doctor/tasks/{task_id})
    # ---------------------------------------------------------
    print(f"\n[5] Deleting the Urgent task...")
    res_delete = requests.delete(f"{BASE_URL}/doctor/tasks/{urgent_task_id}", headers=doc_headers)
    
    if res_delete.status_code == 204:
        print("   ✅ SUCCESS: Task successfully deleted (204 No Content).")
    else:
        print(f"   ❌ FAILED: Task deletion returned {res_delete.status_code}. {res_delete.text}")

    print("\n" + "="*60)
    print("🏁 Doctor Tasks Flow Test Complete")
    print("="*60)

if __name__ == "__main__":
    test_tasks_flow()