"""
Calendar API Test Suite
Tests all 8 calendar endpoints using a doctor token.
Run inside Docker: docker exec saramedico_backend python /app/test_calendar_api.py
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/v1"
DOCTOR_EMAIL = f"testdoc_cal_{datetime.now().strftime('%H%M%S')}@example.com"
DOCTOR_PASSWORD = "TestPass@1234"
DOCTOR_TOKEN = None
EVENT_ID = None

# Reusable date helpers
TODAY = datetime.utcnow()
START_DATE = TODAY.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
END_DATE = (TODAY + timedelta(days=30)).replace(hour=23, minute=59, second=59).isoformat()

# Event time: tomorrow 10AM - 11AM
EVENT_START = (TODAY + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0).isoformat()
EVENT_END   = (TODAY + timedelta(days=1)).replace(hour=11, minute=0, second=0, microsecond=0).isoformat()


def sep(title=""):
    print(f"\n{'='*60}")
    if title:
        print(f"  {title}")
        print('='*60)


def p(label, resp):
    ok = "✅" if resp.ok else "❌"
    print(f"{ok} {label}: {resp.status_code}")
    try:
        data = resp.json()
        # Print compactly — show first 300 chars only
        txt = json.dumps(data, indent=2)
        print(txt[:300] + ("..." if len(txt) > 300 else ""))
    except Exception:
        print(resp.text[:300])
    return resp.json() if resp.ok else None


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 1: Auth
# ─────────────────────────────────────────────────────────────────────────────
sep("PHASE 1: Doctor Auth Setup")

print(f"\n--- Registering Doctor ({DOCTOR_EMAIL}) ---")
reg = requests.post(f"{BASE_URL}/auth/register", json={
    "email": DOCTOR_EMAIL,
    "password": DOCTOR_PASSWORD,
    "full_name": "Dr. Calendar Tester",
    "role": "doctor"
})
print(f"{'✅' if reg.ok else '❌'} Register: {reg.status_code}")

print("\n--- Logging in Doctor ---")
login = requests.post(f"{BASE_URL}/auth/login", json={
    "email": DOCTOR_EMAIL,
    "password": DOCTOR_PASSWORD
})
if not login.ok:
    print(f"❌ Login failed: {login.status_code} — {login.text}")
    exit(1)

DOCTOR_TOKEN = login.json()["access_token"]
HEADERS = {"Authorization": f"Bearer {DOCTOR_TOKEN}"}
print(f"✅ Login: {login.status_code} — Token acquired")


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 2: Calendar CRUD
# ─────────────────────────────────────────────────────────────────────────────
sep("PHASE 2: Calendar CRUD Endpoints")

# 1. GET /calendar/events (date range — empty initially)
print("\n--- 1. GET /calendar/events (date range list) ---")
resp = requests.get(f"{BASE_URL}/calendar/events", headers=HEADERS, params={
    "start_date": START_DATE,
    "end_date": END_DATE,
})
p("GET /calendar/events", resp)

# 2. POST /calendar/events
print("\n--- 2. POST /calendar/events (create custom event) ---")
create_resp = requests.post(f"{BASE_URL}/calendar/events", headers=HEADERS, json={
    "title": "Team Sync Meeting",
    "description": "Weekly doctor's team sync and patient review",
    "start_time": EVENT_START,
    "end_time": EVENT_END,
    "event_type": "custom",
    "color": "#4A90E2",
    "reminder_minutes": 15,
    "all_day": False
})
data = p("POST /calendar/events", create_resp)
if data:
    EVENT_ID = data.get("id")
    print(f"  → Created event ID: {EVENT_ID}")
else:
    print("⚠️  Event creation failed — remaining tests may fail.")

# 3. GET /calendar/events/{event_id}
print(f"\n--- 3. GET /calendar/events/{{event_id}} ---")
if EVENT_ID:
    resp = requests.get(f"{BASE_URL}/calendar/events/{EVENT_ID}", headers=HEADERS)
    p("GET /calendar/events/{event_id}", resp)
else:
    print("⚠️  Skipped — no event_id available")

# 4. PUT /calendar/events/{event_id}
print(f"\n--- 4. PUT /calendar/events/{{event_id}} (update title & description) ---")
if EVENT_ID:
    resp = requests.put(f"{BASE_URL}/calendar/events/{EVENT_ID}", headers=HEADERS, json={
        "title": "Updated Team Sync Meeting",
        "description": "Updated: Monthly review added to agenda",
        "color": "#FF6B6B",
        "reminder_minutes": 30
    })
    p("PUT /calendar/events/{event_id}", resp)
else:
    print("⚠️  Skipped — no event_id available")


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 3: View Endpoints
# ─────────────────────────────────────────────────────────────────────────────
sep("PHASE 3: View Endpoints")

# 5. GET /calendar/day/{date}
tomorrow_date = (TODAY + timedelta(days=1)).strftime("%Y-%m-%d")
print(f"\n--- 5. GET /calendar/day/{tomorrow_date} ---")
resp = requests.get(f"{BASE_URL}/calendar/day/{tomorrow_date}", headers=HEADERS)
data = p(f"GET /calendar/day/{tomorrow_date}", resp)
if data:
    print(f"  → Events on {tomorrow_date}: {data.get('total_count', 0)}")

# 6. GET /calendar/month/{year}/{month}
year = TODAY.year
month = TODAY.month
print(f"\n--- 6. GET /calendar/month/{year}/{month} ---")
resp = requests.get(f"{BASE_URL}/calendar/month/{year}/{month}", headers=HEADERS)
data = p(f"GET /calendar/month/{year}/{month}", resp)
if data:
    print(f"  → Total events this month: {data.get('total_events', 0)}")

# 7. GET /calendar/organization/events
print("\n--- 7. GET /calendar/organization/events ---")
resp = requests.get(f"{BASE_URL}/calendar/organization/events", headers=HEADERS, params={
    "start_date": START_DATE,
    "end_date": END_DATE,
})
data = p("GET /calendar/organization/events", resp)
if data is not None:
    print(f"  → Org events found: {len(data) if isinstance(data, list) else 'N/A'}")


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 4: Cleanup — Delete
# ─────────────────────────────────────────────────────────────────────────────
sep("PHASE 4: DELETE Calendar Event")

print(f"\n--- 8. DELETE /calendar/events/{{event_id}} ---")
if EVENT_ID:
    resp = requests.delete(f"{BASE_URL}/calendar/events/{EVENT_ID}", headers=HEADERS)
    if resp.status_code == 204:
        print(f"✅ DELETE /calendar/events/{{event_id}}: 204 No Content — event deleted")
    else:
        print(f"❌ DELETE failed: {resp.status_code} — {resp.text}")

    # Verify it's gone
    print("\n--- Verifying deletion (GET should return 404) ---")
    verify = requests.get(f"{BASE_URL}/calendar/events/{EVENT_ID}", headers=HEADERS)
    if verify.status_code == 404:
        print("✅ Confirmed: Event is gone (404)")
    else:
        print(f"⚠️  Unexpected: {verify.status_code} — {verify.text[:200]}")
else:
    print("⚠️  Skipped — no event_id available")

sep("CALENDAR API TEST COMPLETE")
