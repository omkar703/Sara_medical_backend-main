import requests
import json
import uuid
import time
from datetime import datetime

BASE_URL = "http://[::1]:8000/api/v1/auth"

# Test Data
unique_id = str(uuid.uuid4())[:8]
TEST_USER = {
    "email": f"test_auth_{unique_id}@example.com",
    "password": "SecurePassword123!",
    "confirm_password": "SecurePassword123!",
    "first_name": "Test",
    "last_name": "AuthUser",
    "role": "doctor",
    "organization_name": "Test Org",
    "date_of_birth": "1990-01-01"
}

STATE = {
    "access_token": None,
    "refresh_token": None,
}

def print_header(title):
    print(f"\n{'='*50}")
    print(f"  {title.upper()}")
    print(f"{'='*50}")

def print_response(response):
    print(f"Status Code: {response.status_code}")
    try:
        data = response.json()
        print("Response Body:")
        print(json.dumps(data, indent=2))
        return data
    except Exception:
        print(f"Raw Response: {response.text}")
        return None

def test_register():
    print_header("Register User (/register)")
    url = f"{BASE_URL}/register"
    print(f"POST {url}")
    print(f"Payload: {json.dumps(TEST_USER, indent=2)}")
    
    response = requests.post(url, json=TEST_USER)
    return print_response(response)

def test_login():
    print_header("Login User (/login)")
    url = f"{BASE_URL}/login"
    payload = {
        "email": TEST_USER["email"],
        "password": TEST_USER["password"]
    }
    print(f"POST {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    response = requests.post(url, json=payload)
    data = print_response(response)
    
    if response.status_code == 200 and data:
        STATE["access_token"] = data.get("access_token")
        STATE["refresh_token"] = data.get("refresh_token")
        print("\n✅ Tokens saved to state.")
    return data

def test_verify_email():
    print_header("Verify Email (/verify-email)")
    print("⚠️ Note: This endpoint requires a valid token from an email to test properly in isolation.")
    print("Testing with dummy token to verify endpoint existence and 4xx handling.")
    url = f"{BASE_URL}/verify-email"
    payload = {"token": "dummy_verification_token"}
    print(f"POST {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    response = requests.post(url, json=payload)
    return print_response(response)

def test_verify_mfa_setup():
    print_header("Verify MFA Setup (/verify-mfa-setup)")
    print("⚠️ Note: This requires the /setup-mfa API to be called first to get a code.")
    print("Testing with dummy code to verify endpoint existence.")
    url = f"{BASE_URL}/verify-mfa-setup"
    payload = {"code": "123456"}
    headers = {"Authorization": f"Bearer {STATE['access_token']}"} if STATE['access_token'] else {}
    print(f"POST {url}")
    
    response = requests.post(url, json=payload, headers=headers)
    return print_response(response)

def test_get_me():
    print_header("Get Current User (/me)")
    url = f"{BASE_URL}/me"
    headers = {"Authorization": f"Bearer {STATE['access_token']}"}
    print(f"GET {url}")
    print(f"Headers: {json.dumps(headers, indent=2)}")
    
    response = requests.get(url, headers=headers)
    return print_response(response)

def test_refresh_token():
    print_header("Refresh Token (/refresh)")
    url = f"{BASE_URL}/refresh"
    payload = {"refresh_token": STATE["refresh_token"]}
    print(f"POST {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    response = requests.post(url, json=payload)
    data = print_response(response)
    
    if response.status_code == 200 and data:
        STATE["access_token"] = data.get("access_token")
        print("\n✅ New Access Token saved to state.")
    return data

def test_forgot_password():
    print_header("Forgot Password (/forgot-password)")
    url = f"{BASE_URL}/forgot-password"
    payload = {"email": TEST_USER["email"]}
    print(f"POST {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    response = requests.post(url, json=payload)
    return print_response(response)

def test_reset_password():
    print_header("Reset Password (/reset-password)")
    print("⚠️ Note: This endpoint requires a valid reset token from a real email flow.")
    print("Testing with dummy token to verify endpoint existence and 4xx handling.")
    url = f"{BASE_URL}/reset-password"
    payload = {
        "token": "dummy_reset_token",
        "new_password": "NewSecurePassword123!",
        "confirm_password": "NewSecurePassword123!"
    }
    print(f"POST {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    response = requests.post(url, json=payload)
    return print_response(response)

def test_google_login():
    print_header("Google Login (/google/login)")
    url = f"{BASE_URL}/google/login"
    print(f"GET {url}")
    
    response = requests.get(url, allow_redirects=False) # Prevent following auth redirects
    print(f"Status Code: {response.status_code}")
    print(f"Redirect Location: {response.headers.get('Location', 'None')}")
    
def test_google_callback():
    print_header("Google Callback (/google/callback)")
    print("⚠️ Note: This endpoint requires a valid Google Code/State in the query. Testing for 400 error.")
    url = f"{BASE_URL}/google/callback?code=dummy&state=dummy"
    print(f"GET {url}")
    
    response = requests.get(url)
    return print_response(response)

def test_logout():
    print_header("Logout (/logout)")
    url = f"{BASE_URL}/logout"
    headers = {"Authorization": f"Bearer {STATE['access_token']}"}
    print(f"POST {url}")
    print(f"Headers: {json.dumps(headers, indent=2)}")
    
    response = requests.post(url, headers=headers)
    return print_response(response)

def run_all_tests():
    print(f"Starting Auth API Tests at {datetime.now()}")
    print(f"Targeting BASE_URL: {BASE_URL}")
    print("Ensure the backend server is running!\n")
    
    # Run the tests in logical order
    test_register()
    test_login()
    
    if STATE["access_token"]:
        test_get_me()
        test_verify_mfa_setup()
        test_refresh_token()
        
    test_verify_email()
    test_forgot_password()
    test_reset_password()
    
    test_google_login()
    test_google_callback()
    
    if STATE["access_token"]:
        test_logout()

    print("\n✅ All endpoint tests completed.")

if __name__ == "__main__":
    try:
        run_all_tests()
    except requests.exceptions.ConnectionError:
        print("\n❌ CONNECTION ERROR: Could not connect to the backend server.")
        print("Please ensure the backend API is running at http://localhost:8000")
