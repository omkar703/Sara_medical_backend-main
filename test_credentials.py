import asyncio
import json
import httpx
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import create_access_token
from datetime import timedelta
import os
import sys

async def test_credentials():
    print("=== VISION OCR CREDENTIAL TEST ===\n")
    
    # 1. Get auth token (though endpoint doesn't strictly check right now, good practice if we add deps later)
    # The prompt actually didn't explicitly mandate auth for this endpoint, but it's part of the app.
    # The endpoint implementation does NOT have `current_user = Depends(get_current_active_user)` in our added code.
    # It just accepts the image. Let's just call it directly.
    
    base_url = "http://localhost:8000/api/v1"
    
    files_to_test = [
        "/app/MBBS-DEGREE-rotated-1.jpg",
        "/app/MD-DEGREE-rotated-1.jpg"
    ]
    
    for file_path in files_to_test:
        file_name = os.path.basename(file_path)
        print(f"--- Processing {file_name} ---")
        
        if not os.path.exists(file_path):
            print(f"ERROR: File {file_path} not found.")
            continue
            
        with open(file_path, "rb") as f:
            # Send file as 'certificate_image' parameter
            files = {"certificate_image": (file_name, f, "image/jpeg")}
            
            try:
                # We use a longer timeout because Claude Vision can take a few seconds
                resp = httpx.post(
                    f"{base_url}/doctor/extract-credentials", 
                    files=files, 
                    timeout=30.0
                )
                print("Status Code:", resp.status_code)
                try:
                    json_resp = resp.json()
                    print(json.dumps(json_resp, indent=2))
                except Exception as e:
                    print("Could not parse JSON response:", resp.text)
            except Exception as e:
                print("HTTP Request failed:", e)
        print()

if __name__ == "__main__":
    asyncio.run(test_credentials())
