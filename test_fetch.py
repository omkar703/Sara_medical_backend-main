import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = "http://107.20.98.130:8000/api/v1/auth/login"
data = json.dumps({"email": "doctor@test.com", "password": "test123"}).encode('utf-8')
req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

try:
    with urllib.request.urlopen(req, context=ctx) as response:
        resp_data = json.loads(response.read().decode())
        token = resp_data["access_token"]
        print("Logged in")
        
    req2 = urllib.request.Request("http://107.20.98.130:8000/api/v1/doctor/patients", headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req2, context=ctx) as response2:
        patients = json.loads(response2.read().decode())
        print("Patients:", patients)
except urllib.error.HTTPError as e:
    print("Error:", e.code, e.reason, e.read().decode())
except Exception as e:
    print("Error:", str(e))
