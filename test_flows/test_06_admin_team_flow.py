import requests
import psycopg2
import uuid

BASE_URL = "http://localhost:8000/api/v1"

# Database credentials based on your docker-compose.yml
DB_CONFIG = {
    "dbname": "saramedico_dev",
    "user": "saramedico_user",
    "password": "SaraMed1c0_Dev_2024!Secure",
    "host": "localhost",
    "port": "5435"
}

def clean_database(emails):
    print("\n[Database Cleanup] Removing existing test users and invites...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        for email in emails:
            cur.execute("DELETE FROM users WHERE email = %s;", (email,))
            cur.execute("DELETE FROM invitations WHERE email = %s;", (email,))
        conn.commit()
        cur.close()
        conn.close()
        print(f"   ✅ SUCCESS: Cleaned up database for {emails}")
    except Exception as e:
        print(f"   ⚠️ WARNING: Database cleanup failed. Error: {e}")

def test_admin_team_flow():
    print("="*60)
    print("🧪 STARTING: Admin, Organization & Team Management Flow Test")
    print("="*60)

    admin_email = "super_admin@saramedico.com"
    invitee_email = "new_doctor_invite@saramedico.com"
    password = "SecurePass123!"

    # 0. Clean the DB first
    clean_database([admin_email, invitee_email])

    # ---------------------------------------------------------
    # Setup: Register and Login as Admin
    # ---------------------------------------------------------
    print("\n[Setup] Registering and authenticating Admin...")
    requests.post(f"{BASE_URL}/auth/register", json={
        "email": admin_email, "password": password, 
        "full_name": "Hospital Administrator", "role": "admin",
        "organization_name": "Saramedico Central Hospital"
    })
    
    admin_login = requests.post(f"{BASE_URL}/auth/login", json={"email": admin_email, "password": password})
    if admin_login.status_code != 200:
        print(f"   ❌ FAILED: Admin login. {admin_login.text}")
        return
        
    admin_token = admin_login.json().get("access_token")
    # Get the organization ID from the admin profile to use in the invite payload
    admin_profile_res = requests.get(f"{BASE_URL}/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
    admin_org_id = admin_profile_res.json().get("organization_id")
    
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print("   ✅ Setup Complete.")

    # ---------------------------------------------------------
    # 1. Update Organization Settings (PATCH /admin/settings/organization)
    # ---------------------------------------------------------
    print("\n[1] Updating Organization Settings...")
    org_settings_payload = {
        "name": "Saramedico Central Hospital - Updated",
        "timezone": "EST",
        "date_format": "MM/DD/YYYY"
    }
    
    res_org = requests.patch(f"{BASE_URL}/admin/settings/organization", headers=admin_headers, json=org_settings_payload)
    if res_org.status_code == 200:
        print("   ✅ SUCCESS: Organization settings updated.")
    else:
        print(f"   ❌ FAILED: Org update returned {res_org.status_code}. {res_org.text}")
        return

    # ---------------------------------------------------------
    # 2. Fetch Team Roles (GET /team/roles)
    # ---------------------------------------------------------
    print("\n[2] Fetching available team roles...")
    res_roles = requests.get(f"{BASE_URL}/team/roles", headers=admin_headers)
    if res_roles.status_code == 200:
        roles = res_roles.json()
        print(f"   ✅ SUCCESS: Found {len(roles)} team roles available.")
    else:
        print(f"   ❌ FAILED: Roles fetch returned {res_roles.status_code}. {res_roles.text}")

    # ---------------------------------------------------------
    # 3. Invite a Team Member (POST /team/invite)
    # ---------------------------------------------------------
    print("\n[3] Sending invitation to a new staff member...")
    # Add the required fields based on the Pydantic schema
    invite_payload = {
        "email": invitee_email,
        "full_name": "Dr. Newbie",
        "role": "MEMBER",
        "department_id": admin_org_id or str(uuid.uuid4()), # Use org_id, or fallback to mock
        "department_role": "Senior Physician"
    }
    
    res_invite = requests.post(f"{BASE_URL}/team/invite", headers=admin_headers, json=invite_payload)
    if res_invite.status_code == 201:
        invite_data = res_invite.json()
        invite_id = invite_data.get("invitation_id")
        print(f"   ✅ SUCCESS: Invitation sent. Invite ID: {invite_id}")
    else:
        print(f"   ❌ FAILED: Inviting member returned {res_invite.status_code}. {res_invite.text}")
        return

    # ---------------------------------------------------------
    # 4. View Pending Invites (GET /team/invites/pending)
    # ---------------------------------------------------------
    print("\n[4] Checking the Pending Invites list...")
    res_pending = requests.get(f"{BASE_URL}/team/invites/pending", headers=admin_headers)
    if res_pending.status_code == 200:
        pending_list = res_pending.json()
        print(f"   ✅ SUCCESS: Found {len(pending_list)} pending invite(s).")
        if any(inv.get("email") == invitee_email for inv in pending_list):
            print("   ✅ SUCCESS: New doctor's invite successfully appears in the pending queue.")
    else:
        print(f"   ❌ FAILED: Fetching pending invites returned {res_pending.status_code}. {res_pending.text}")

    # ---------------------------------------------------------
    # 5. Fetch Admin Dashboard Overview (GET /admin/overview)
    # ---------------------------------------------------------
    print("\n[5] Fetching Admin Dashboard Overview...")
    res_overview = requests.get(f"{BASE_URL}/admin/overview", headers=admin_headers)
    if res_overview.status_code == 200:
        overview = res_overview.json()
        activity_count = len(overview.get("recent_activity", []))
        print(f"   ✅ SUCCESS: Admin Overview fetched. Found {activity_count} recent activity logs.")
    else:
        print(f"   ❌ FAILED: Dashboard overview returned {res_overview.status_code}. {res_overview.text}")

    # ---------------------------------------------------------
    # 6. Revoke the Invitation (DELETE /admin/accounts/{id})
    # ---------------------------------------------------------
    print("\n[6] Revoking the pending invitation...")
    res_revoke = requests.delete(f"{BASE_URL}/admin/accounts/{invite_id}", headers=admin_headers)
    if res_revoke.status_code == 200:
        print(f"   ✅ SUCCESS: Invitation successfully revoked (Status: {res_revoke.json().get('status')}).")
    else:
        print(f"   ❌ FAILED: Revoking invite returned {res_revoke.status_code}. {res_revoke.text}")

    print("\n" + "="*60)
    print("🏁 Admin, Organization & Team Management Flow Test Complete")
    print("="*60)

if __name__ == "__main__":
    test_admin_team_flow()