import asyncio
import httpx
import uuid
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/v1"

async def test_notifications_flow():
    print("\n=== STARTING NOTIFICATION SYSTEM TEST ===\n")
    async with httpx.AsyncClient(timeout=10.0) as client:
        # --- 1. Doctor Panel Notification Integration ---
        print("\n[DOCTOR PANEL TEST]")
        doc_email = f"doc_notif_{uuid.uuid4().hex[:4]}@test.com"
        print(f"[*] Registering & Logging in Doctor: {doc_email}...")
        
        # Registration
        reg_resp = await client.post(f"{BASE_URL}/auth/register", json={
            "email": doc_email,
            "password": "SecurePass123!",
            "full_name": "Dr. Notification Tester",
            "role": "doctor",
            "organization_name": "General Hospital",
            "phone_number": "+911234567890"
        })
        if reg_resp.status_code not in [200, 201]:
            print(f"FAILED Registration: {reg_resp.text}")
            return

        # Login
        login_resp = await client.post(f"{BASE_URL}/auth/login", json={"email": doc_email, "password": "SecurePass123!"})
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Login Successful.")

        # Simulate a notification-triggering event: Create a Calendar Event
        print("[*] Creating a Calendar Event to trigger a notification...")
        event_resp = await client.post(f"{BASE_URL}/calendar/events", headers=headers, json={
            "title": "Medical Conference",
            "description": "Discussing new AI insights.",
            "start_time": (datetime.utcnow() + timedelta(days=1)).isoformat() + "Z",
            "end_time": (datetime.utcnow() + timedelta(days=1, hours=1)).isoformat() + "Z",
            "all_day": False,
            "color": "#3B82F6",
            "reminder_minutes": 30
        })
        if event_resp.status_code not in [200, 201]:
            print(f"FAILED Event Creation: {event_resp.text}")
            return
        print("✅ Calendar Event Created.")

        # Fetch Notifications
        print("[*] Fetching Dr. Notifications via API...")
        notif_resp = await client.get(f"{BASE_URL}/notifications", headers=headers)
        if notif_resp.status_code == 200:
            notifs = notif_resp.json()
            print(f"✅ Received {len(notifs)} notification(s).")
            if len(notifs) > 0:
                print(f"   LATEST: [{notifs[0]['type']}] {notifs[0]['title']}: {notifs[0]['message']}")
        else:
            print(f"FAILED to fetch notifications: {notif_resp.text}")

        # --- 2. Hospital Panel Notification Integration ---
        print("\n[HOSPITAL PANEL TEST]")
        hosp_email = f"hosp_notif_{uuid.uuid4().hex[:4]}@hospital.com"
        print(f"[*] Registering & Logging in Hospital Admin: {hosp_email}...")
        
        # Register Hospital
        hosp_reg_resp = await client.post(f"{BASE_URL}/auth/register", json={
            "email": hosp_email,
            "password": "HospitalPass123!",
            "full_name": "Admin Sara Hospital",
            "role": "hospital",
            "organization_name": "Sara Central Hospital",
            "phone_number": "+918888777766"
        })
        
        # Login Hospital
        hosp_login_resp = await client.post(f"{BASE_URL}/auth/login", json={"email": hosp_email, "password": "HospitalPass123!"})
        hosp_token = hosp_login_resp.json()["access_token"]
        hosp_headers = {"Authorization": f"Bearer {hosp_token}"}
        print("✅ Hospital Login Successful.")

        # Simulate Hospital Event: Create organization-level event
        print("[*] Creating a Hospital-wide event...")
        h_event_resp = await client.post(f"{BASE_URL}/calendar/events", headers=hosp_headers, json={
            "title": "Hospital Annual Staff Meeting",
            "description": "Quarterly health review.",
            "start_time": (datetime.utcnow() + timedelta(days=2)).isoformat() + "Z",
            "end_time": (datetime.utcnow() + timedelta(days=2, hours=2)).isoformat() + "Z",
            "all_day": False,
            "color": "#10B981"
        })
        print(f"✅ Hospital Event Created. Status: {h_event_resp.status_code}")

        # Fetch Hospital Notifications
        print("[*] Fetching Hospital Notifications via API...")
        h_notif_resp = await client.get(f"{BASE_URL}/notifications", headers=hosp_headers)
        if h_notif_resp.status_code == 200:
            h_notifs = h_notif_resp.json()
            print(f"✅ Received {len(h_notifs)} notification(s) for Hospital.")
            if len(h_notifs) > 0:
                print(f"   LATEST: [{h_notifs[0]['type']}] {h_notifs[0]['title']}")
        else:
            print(f"FAILED to fetch hospital notifications: {h_notif_resp.text}")

        print("\n=== TEST COMPLETED SUCCESSFULLY ===\n")

if __name__ == "__main__":
    asyncio.run(test_notifications_flow())
