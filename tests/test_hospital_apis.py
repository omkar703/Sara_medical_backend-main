import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000/api/v1"

async def test_hospital_apis():
    print("\n=== STARTING HOSPITAL API SYSTEM TEST ===\n")
    async with httpx.AsyncClient(timeout=10.0) as client:
        # 1. Login to get token
        print("[*] Logging in as Hospital Admin...")
        login_resp = await client.post(f"{BASE_URL}/auth/login", json={
            "email": "hosp_notif_5cb2@hospital.com",
            "password": "HospitalPass123!"
        })
        
        if login_resp.status_code != 200:
            print(f"FAILED Login: {login_resp.text}")
            return
            
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        print("✅ Login Successful.")

        # 2. Get Departments
        print("\n[*] GET /organization/departments")
        dept_resp = await client.get(f"{BASE_URL}/organization/departments", headers=headers)
        if dept_resp.status_code == 200:
            print(f"✅ Received departments: {dept_resp.json().get('departments')}")
        else:
            print(f"FAILED to fetch departments: {dept_resp.text}")

        # 3. Create Doctor
        print("\n[*] POST /hospital/doctor/create")
        doc_email = f"dr.test.{json.dumps(asyncio.get_event_loop().time()).split('.')[0]}@hospital.com"
        create_resp = await client.post(f"{BASE_URL}/hospital/doctor/create", headers=headers, json={
            "email": doc_email,
            "password": "SecurePassword123!",
            "name": "Dr. Integration Test",
            "department": "Neurology",
            "department_role": "Senior Consultant",
            "license_number": f"MED-{json.dumps(asyncio.get_event_loop().time()).split('.')[0]}"
        })
        
        if create_resp.status_code == 200:
            doc_id = create_resp.json().get("doctor_id")
            print(f"✅ Doctor created successfully. ID: {doc_id}")
            
            # 4. Update Doctor Profile
            print(f"\n[*] PATCH /hospital/doctor/{doc_id}")
            update_resp = await client.patch(f"{BASE_URL}/hospital/doctor/{doc_id}", headers=headers, json={
                "department_role": "Head of Neurology"
            })
            if update_resp.status_code == 200:
                print(f"✅ Doctor updated successfully: {update_resp.json().get('message')}")
            else:
                print(f"FAILED to update doctor: {update_resp.text}")

            # 5. Get Doctors By Department
            print("\n[*] GET /doctors/by-department?department=Neurology")
            list_resp = await client.get(f"{BASE_URL}/doctors/by-department", headers=headers, params={"department": "Neurology"})
            if list_resp.status_code == 200:
                results = list_resp.json().get("results", [])
                print(f"✅ Received {len(results)} doctor(s) for Neurology.")
                for d in results:
                    print(f"   - {d['name']} ({d['department_role']})")
            else:
                print(f"FAILED to fetch doctors by department: {list_resp.text}")

        else:
            print(f"FAILED to create doctor: {create_resp.text}")

    print("\n=== HOSPITAL API TEST COMPLETED ===\n")

if __name__ == "__main__":
    asyncio.run(test_hospital_apis())
