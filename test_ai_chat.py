import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

# Credentials
DOCTOR_EMAIL = "doctor@test.com"
PASSWORD = "test1234"

def login():
    """Login and get access token."""
    print("Logging in...")
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "email": DOCTOR_EMAIL,
        "password": PASSWORD
    })
    
    if response.status_code == 200:
        print("Login successful.")
        return response.json().get("access_token")
    else:
        print(f"Login failed: {response.text}")
        return None

def test_ai_chat(token):
    """Test the AI chat endpoint."""
    print("\nStarting AI Chat Request...")
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "text/event-stream"
    }
    
    payload = {
        "query": "Hello, can you help me with a patient?"
    }
    
    # Send streaming request
    print("Sending request to /doctor/ai/chat/doctor...")
    response = requests.post(
        f"{BASE_URL}/doctor/ai/chat/doctor", 
        json=payload, 
        headers=headers, 
        stream=True
    )
    
    if response.status_code != 200:
        print(f"Request failed with status {response.status_code}: {response.text}")
        return
        
    print("Response Stream:")
    print("-" * 50)
    
    # The endpoint returns a streaming response. Sometimes it's SSE, sometimes just text chunks.
    # Let's read it chunk by chunk or decode lines.
    
    try:
        # Fallback to reading raw lines
        response = requests.post(
            f"{BASE_URL}/doctor/ai/chat/doctor", 
            json=payload, 
            headers=headers, 
            stream=True
        )
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                if decoded_line.startswith('data: '):
                    print(decoded_line[6:], end="", flush=True)
                else:
                    print(decoded_line)
                
    except Exception as e:
        print(f"\nError: {e}")
                
    print("\n" + "-" * 50)
    print("Request finished.")

if __name__ == "__main__":
    token = login()
    if token:
        test_ai_chat(token)
