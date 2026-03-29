import requests

BASE_URL = "http://107.20.98.130:8000/api/v1"

login_data = {
    "email": "doctor@test.com",
    "password": "test123"
}

resp = requests.post(f"{BASE_URL}/auth/login", json=login_data)
if not resp.ok:
    print("Login failed:", resp.text)
    exit(1)

token = resp.json()["access_token"]
print("Logged in!")

headers = {"Authorization": f"Bearer {token}"}
resp = requests.get(f"{BASE_URL}/doctor/patients", headers=headers)
print("Patients status:", resp.status_code)
if resp.ok:
    print("Patients:", resp.json())
else:
    print("Error:", resp.text)

