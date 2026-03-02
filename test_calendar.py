import asyncio
import httpx
import json
from datetime import datetime, timedelta, timezone

BASE_URL = "http://localhost:8000/api/v1"
TEST_EMAIL = "hospital@test.com"
TEST_PASSWORD = "test1234"

async def test_calendar_endpoints():
    print("\n--- 1. Authenticating ---")
    async with httpx.AsyncClient(timeout=10.0) as client:
        login_resp = await client.post(f"{BASE_URL}/auth/login", json={
            "email": TEST_EMAIL, "password": TEST_PASSWORD
        })
        
        if login_resp.status_code != 200:
            print(f"Login Failed: {login_resp.text}")
            return
            
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("Authenticated successfully as Hospital Manager.")

        # --- Test 1: Create a Custom Calendar Event ---
        print("\n--- 2. POST /calendar/events (Create Event) ---")
        now = datetime.now(timezone.utc)
        event_payload = {
            "title": "Team Sync Meeting",
            "description": "Weekly alignment",
            "start_time": (now + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "end_time": (now + timedelta(days=1, hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "all_day": False,
            "event_type": "custom",
            "color": "#3B82F6",
            "reminder_minutes": 15
        }
        resp = await client.post(f"{BASE_URL}/calendar/events", headers=headers, json=event_payload)
        print(f"Status: {resp.status_code}")
        event_data = resp.json() if resp.status_code == 201 else {}
        print(json.dumps(event_data, indent=2) if resp.status_code == 201 else resp.text)

        # --- Test 2: Get Events ---
        print("\n--- 3. GET /calendar/events (List Events) ---")
        start_str = (now - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
        end_str = (now + timedelta(days=14)).strftime("%Y-%m-%dT%H:%M:%SZ")
        resp = await client.get(
            f"{BASE_URL}/calendar/events?start_date={start_str}&end_date={end_str}", 
            headers=headers
        )
        print(f"Status: {resp.status_code}")
        print(json.dumps(resp.json(), indent=2) if resp.status_code == 200 else resp.text)

        # --- Test 3: Get Day View ---
        print("\n--- 4. GET /calendar/day/{date} (Day View) ---")
        target_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")
        resp = await client.get(f"{BASE_URL}/calendar/day/{target_date}", headers=headers)
        print(f"Status: {resp.status_code}")
        print(json.dumps(resp.json(), indent=2) if resp.status_code == 200 else resp.text)

        # --- Test 4: Get Month View ---
        print("\n--- 5. GET /calendar/month/{year}/{month} (Month View) ---")
        resp = await client.get(f"{BASE_URL}/calendar/month/{now.year}/{now.month}", headers=headers)
        print(f"Status: {resp.status_code}")
        print(json.dumps(resp.json(), indent=2) if resp.status_code == 200 else resp.text)

        # --- Test 5: Organization Events ---
        print("\n--- 6. GET /calendar/organization/events ---")
        resp = await client.get(
            f"{BASE_URL}/calendar/organization/events?start_date={start_str}&end_date={end_str}", 
            headers=headers
        )
        print(f"Status: {resp.status_code}")
        events = resp.json() if resp.status_code == 200 else []
        print(f"Found {len(events)} organization events.")
        if events:
             print(json.dumps(events[0], indent=2))

async def main():
    await test_calendar_endpoints()

if __name__ == "__main__":
    asyncio.run(main())
