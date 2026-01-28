import httpx
import json

BASE_URL = "http://localhost:8001/api/v1"

def test_api():
    # 1. Login
    print("\n--- 1. Authenticating as Doctor ---")
    # Using the credentials from our seeding script
    login_data = {"email": "doctor_e2e_final@test.com", "password": "Password123"}
    try:
        resp = httpx.post(f"{BASE_URL}/auth/login", json=login_data, timeout=10.0)
        if resp.status_code != 200:
            print(f"Login failed (Status {resp.status_code}): {resp.text}")
            return
        
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("Authentication Successful.")
    except Exception as e:
        print(f"Error during login: {e}")
        return

    # 2. Get Next Appointment
    print("\n--- 2. GET /doctor/schedule/next ---")
    try:
        resp = httpx.get(f"{BASE_URL}/doctor/schedule/next", headers=headers, timeout=10.0)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print(json.dumps(resp.json(), indent=2))
        else:
            print(f"Error: {resp.text}")
    except Exception as e:
        print(f"Error fetching next appointment: {e}")

    # 3. List Roles
    print("\n--- 3. GET /team/roles ---")
    try:
        resp = httpx.get(f"{BASE_URL}/team/roles", headers=headers, timeout=10.0)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print(json.dumps(resp.json(), indent=2))
        else:
            print(f"Error: {resp.text}")
    except Exception as e:
        print(f"Error fetching roles: {e}")

    # 4. Invite Team Member
    print("\n--- 4. POST /team/invite ---")
    invite_data = {
        "full_name": "Nurse Joy",
        "email": "nurse_joy_2@pokemon.com",
        "role": "MEMBER"
    }
    try:
        resp = httpx.post(f"{BASE_URL}/team/invite", json=invite_data, headers=headers, timeout=10.0)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 201:
            print(json.dumps(resp.json(), indent=2))
        else:
            print(f"Error: {resp.text}")
    except Exception as e:
        print(f"Error inviting member: {e}")

    # 5. Get Activity Feed
    print("\n--- 5. GET /doctor/activity ---")
    try:
        resp = httpx.get(f"{BASE_URL}/doctor/activity", headers=headers, timeout=10.0)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            activities = resp.json()
            # Just show first few items
            print(json.dumps(activities[:5], indent=2))
        else:
            print(f"Error: {resp.text}")
    except Exception as e:
        print(f"Error fetching activity: {e}")

if __name__ == "__main__":
    test_api()
