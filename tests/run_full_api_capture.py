import asyncio, httpx, uuid, json, sys
from datetime import datetime, timedelta

BASE = "http://backend:8000/api/v1"
RESULTS = {}

def log(name, method, endpoint, req_body, resp_status, resp_body):
    RESULTS[name] = {
        "method": method,
        "endpoint": endpoint,
        "request": req_body,
        "status": resp_status,
        "response": resp_body
    }
    ok = "✅" if resp_status < 400 else "❌"
    print(f"{ok} [{resp_status}] {method} {endpoint}")

async def wait_for_backend(client):
    for _ in range(30):
        try:
            r = await client.get("http://backend:8000/health", timeout=2)
            if r.status_code == 200:
                return True
        except:
            pass
        await asyncio.sleep(2)
    return False

async def main():
    uid = uuid.uuid4().hex[:6]
    doc_email = f"doc_{uid}@saramedico.com"
    pat_email = f"pat_{uid}@saramedico.com"
    admin_email = f"admin_{uid}@saramedico.com"
    password = "SecurePass123!"

    async with httpx.AsyncClient(follow_redirects=True, timeout=30) as c:
        if not await wait_for_backend(c):
            print("Backend not ready"); sys.exit(1)

        # ── HEALTH ──────────────────────────────────────────────
        r = await c.get("http://backend:8000/health")
        log("health", "GET", "/health", None, r.status_code, r.json())

        # ── AUTH: REGISTER DOCTOR ────────────────────────────────
        body = {"email": doc_email, "password": password, "full_name": "Dr. API Test", "role": "doctor", "organization_name": "Test Hospital", "phone_number": "+16502530001"}
        r = await c.post(f"{BASE}/auth/register", json=body)
        log("auth_register_doctor", "POST", "/auth/register", body, r.status_code, r.text[:200])

        # ── AUTH: LOGIN DOCTOR ───────────────────────────────────
        body = {"email": doc_email, "password": password}
        r = await c.post(f"{BASE}/auth/login", json=body)
        log("auth_login", "POST", "/auth/login", body, r.status_code, r.json())
        doc_login = r.json()
        doc_token = doc_login.get("access_token", "")
        doc_id = doc_login.get("user", {}).get("id", "")
        dh = {"Authorization": f"Bearer {doc_token}"}

        # ── AUTH: ME ─────────────────────────────────────────────
        r = await c.get(f"{BASE}/auth/me", headers=dh)
        log("auth_me", "GET", "/auth/me", None, r.status_code, r.json())

        # ── AUTH: REFRESH ────────────────────────────────────────
        ref_token = doc_login.get("refresh_token", "")
        body = {"refresh_token": ref_token}
        r = await c.post(f"{BASE}/auth/refresh", json=body)
        log("auth_refresh", "POST", "/auth/refresh", body, r.status_code, r.json())

        # ── REGISTER ADMIN ───────────────────────────────────────
        body = {"email": admin_email, "password": password, "full_name": "Admin Test", "role": "admin", "organization_name": "Test Hospital Admin", "phone_number": "+16502530002"}
        r = await c.post(f"{BASE}/auth/register", json=body)
        r2 = await c.post(f"{BASE}/auth/login", json={"email": admin_email, "password": password})
        admin_token = r2.json().get("access_token", "")
        ah = {"Authorization": f"Bearer {admin_token}"}

        # ── DOCTOR PROFILE UPDATE ────────────────────────────────
        body = {"specialty": "Cardiology", "license_number": "LIC-TEST-001"}
        r = await c.patch(f"{BASE}/doctor/profile", headers=dh, json=body)
        log("doctor_profile_update", "PATCH", "/doctor/profile", body, r.status_code, r.json())

        # ── PATIENTS: CREATE (ONBOARD) ───────────────────────────
        body = {"fullName": "John Doe Test", "email": pat_email, "password": password, "dateOfBirth": "1985-05-15", "gender": "male", "phoneNumber": "+16502531234"}
        r = await c.post(f"{BASE}/patients", headers=dh, json=body)
        log("patient_create", "POST", "/patients", body, r.status_code, r.json())
        pat_data = r.json()
        pat_id = pat_data.get("id", "")
        log_req = {"fullName": "John Doe Test", "email": "pat_XXXX@saramedico.com", "password": "SecurePass123!", "dateOfBirth": "1985-05-15", "gender": "male", "phoneNumber": "+16502531234"}
        RESULTS["patient_create"]["request"] = log_req

        # ── PATIENTS: LOGIN ──────────────────────────────────────
        r2 = await c.post(f"{BASE}/auth/login", json={"email": pat_email, "password": password})
        pat_token = r2.json().get("access_token", "")
        pat_id_real = r2.json().get("user", {}).get("id", pat_id)
        ph = {"Authorization": f"Bearer {pat_token}"}

        # ── PATIENTS: LIST ───────────────────────────────────────
        r = await c.get(f"{BASE}/patients?page=1&limit=5", headers=dh)
        log("patient_list", "GET", "/patients?page=1&limit=5", None, r.status_code, r.json())

        # ── PATIENTS: GET BY ID ──────────────────────────────────
        if pat_id:
            r = await c.get(f"{BASE}/patients/{pat_id}", headers=dh)
            log("patient_get", "GET", f"/patients/{{patient_id}}", None, r.status_code, r.json())

        # ── DOCTOR: PATIENT DIRECTORY ────────────────────────────
        r = await c.get(f"{BASE}/doctor/patients", headers=dh)
        log("doctor_patients", "GET", "/doctor/patients", None, r.status_code, r.json()[:1] if isinstance(r.json(), list) else r.json())

        # ── DOCTOR: ME/DASHBOARD ─────────────────────────────────
        r = await c.get(f"{BASE}/doctor/me/dashboard", headers=dh)
        log("doctor_dashboard", "GET", "/doctor/me/dashboard", None, r.status_code, r.json())

        # ── DOCTORS: SEARCH ──────────────────────────────────────
        r = await c.get(f"{BASE}/doctors/search?specialty=Cardiology", headers=dh)
        log("doctors_search", "GET", "/doctors/search?specialty=Cardiology", None, r.status_code, r.json())

        # ── CONSULTATIONS: SCHEDULE ──────────────────────────────
        future = (datetime.utcnow() + timedelta(days=1)).isoformat()
        body = {"patientId": pat_id, "scheduledAt": future, "durationMinutes": 30, "notes": "Initial telehealth consultation."}
        r = await c.post(f"{BASE}/consultations", headers=dh, json=body)
        log("consultation_create", "POST", "/consultations", body, r.status_code, r.json())
        cons_data = r.json()
        cons_id = cons_data.get("id", "")

        # ── CONSULTATIONS: LIST ──────────────────────────────────
        r = await c.get(f"{BASE}/consultations?status=scheduled", headers=dh)
        log("consultation_list", "GET", "/consultations?status=scheduled", None, r.status_code, r.json())

        # ── CONSULTATIONS: UPDATE ────────────────────────────────
        if cons_id:
            body = {"status": "completed", "diagnosis": "Hypertension Stage 1", "prescription": "Lisinopril 10mg daily", "notes": "Patient responding well."}
            r = await c.patch(f"{BASE}/consultations/{cons_id}", headers=dh, json=body)
            log("consultation_update", "PATCH", "/consultations/{id}", body, r.status_code, r.json())

        # ── DOCUMENTS: UPLOAD ────────────────────────────────────
        if pat_id:
            files = {"file": ("test_report.pdf", b"%PDF-1.4 fake content", "application/pdf")}
            data = {"patient_id": pat_id, "notes": "Routine Lab Report"}
            r = await c.post(f"{BASE}/documents/upload", headers=dh, data=data, files=files, timeout=30)
            log("document_upload", "POST", "/documents/upload", {"patient_id": pat_id, "notes": "Routine Lab Report", "file": "test_report.pdf"}, r.status_code, r.json())
            doc_id = r.json().get("document_id", "")

            # ── DOCUMENTS: STATUS ────────────────────────────────
            if doc_id:
                r = await c.get(f"{BASE}/documents/{doc_id}/status", headers=dh)
                log("document_status", "GET", "/documents/{id}/status", None, r.status_code, r.json())

        # ── PERMISSIONS: CHECK (no access yet) ──────────────────
        if pat_id_real:
            r = await c.get(f"{BASE}/permissions/check?patient_id={pat_id_real}", headers=dh)
            log("permissions_check_before", "GET", "/permissions/check?patient_id={id}", None, r.status_code, r.json())

            # ── PERMISSIONS: GRANT ───────────────────────────────
            body = {"doctor_id": doc_id, "ai_access_permission": True, "access_level": "read_analyze", "expiry_days": 30, "reason": "Routine access grant"}
            r = await c.post(f"{BASE}/permissions/grant-doctor-access", headers=ph, json=body)
            log("permissions_grant", "POST", "/permissions/grant-doctor-access", body, r.status_code, r.json())

            # ── PERMISSIONS: CHECK (after grant) ─────────────────
            r = await c.get(f"{BASE}/permissions/check?patient_id={pat_id_real}", headers=dh)
            log("permissions_check_after", "GET", "/permissions/check (after grant)", None, r.status_code, r.json())

            # ── PERMISSIONS: REVOKE ──────────────────────────────
            body = {"doctor_id": doc_id}
            r = await c.delete(f"{BASE}/permissions/revoke-doctor-access", headers=ph, json=body)
            log("permissions_revoke", "DELETE", "/permissions/revoke-doctor-access", body, r.status_code, r.json())

        # ── TASKS: CREATE URGENT ─────────────────────────────────
        tomorrow = (datetime.utcnow() + timedelta(days=1)).isoformat()
        body = {"title": "Sign Discharge Papers", "description": "Patient waiting in Room 4.", "due_date": tomorrow, "priority": "urgent", "status": "pending"}
        r = await c.post(f"{BASE}/doctor/tasks", headers=dh, json=body)
        log("task_create", "POST", "/doctor/tasks", body, r.status_code, r.json())
        task_id = r.json().get("id", "")

        # ── TASKS: CREATE NORMAL ─────────────────────────────────
        body2 = {"title": "Review Lab Results", "description": "Check John's blood work.", "due_date": tomorrow, "priority": "normal", "status": "pending"}
        r = await c.post(f"{BASE}/doctor/tasks", headers=dh, json=body2)
        normal_task_id = r.json().get("id", "")

        # ── TASKS: LIST ──────────────────────────────────────────
        r = await c.get(f"{BASE}/doctor/tasks", headers=dh)
        log("task_list", "GET", "/doctor/tasks", None, r.status_code, r.json()[:2] if isinstance(r.json(), list) else r.json())

        # ── TASKS: UPDATE ────────────────────────────────────────
        if task_id:
            body = {"status": "completed"}
            r = await c.patch(f"{BASE}/doctor/tasks/{task_id}", headers=dh, json=body)
            log("task_update", "PATCH", "/doctor/tasks/{id}", body, r.status_code, r.json())

        # ── TASKS: DELETE ────────────────────────────────────────
        if normal_task_id:
            r = await c.delete(f"{BASE}/doctor/tasks/{normal_task_id}", headers=dh)
            log("task_delete", "DELETE", "/doctor/tasks/{id}", None, r.status_code, r.status_code)

        # ── TEAM: ROLES ──────────────────────────────────────────
        r = await c.get(f"{BASE}/team/roles", headers=dh)
        log("team_roles", "GET", "/team/roles", None, r.status_code, r.json())

        # ── TEAM: INVITE ─────────────────────────────────────────
        invite_email = f"invite_{uid}@hospital.com"
        body = {"email": invite_email, "full_name": "Dr. Invited", "role": "MEMBER", "department_id": doc_login.get("user", {}).get("organization_id", str(uuid.uuid4())), "department_role": "Physician"}
        r = await c.post(f"{BASE}/team/invite", headers=dh, json=body)
        log("team_invite", "POST", "/team/invite", body, r.status_code, r.json())
        invite_id = r.json().get("invitation_id", "")

        # ── TEAM: STAFF ──────────────────────────────────────────
        r = await c.get(f"{BASE}/team/staff", headers=dh)
        log("team_staff", "GET", "/team/staff", None, r.status_code, r.json()[:2] if isinstance(r.json(), list) else r.json())

        # ── TEAM: PENDING INVITES ─────────────────────────────────
        r = await c.get(f"{BASE}/team/invites/pending", headers=ah)
        log("team_invites_pending", "GET", "/team/invites/pending", None, r.status_code, r.json())

        # ── ADMIN: OVERVIEW ──────────────────────────────────────
        r = await c.get(f"{BASE}/admin/overview", headers=ah)
        resp = r.json()
        # trim nested lists for brevity
        if isinstance(resp, dict):
            if "recent_activity" in resp: resp["recent_activity"] = resp["recent_activity"][:1]
        log("admin_overview", "GET", "/admin/overview", None, r.status_code, resp)

        # ── ADMIN: SETTINGS ──────────────────────────────────────
        r = await c.get(f"{BASE}/admin/settings", headers=ah)
        log("admin_settings", "GET", "/admin/settings", None, r.status_code, r.json())

        # ── ADMIN: UPDATE ORG SETTINGS ───────────────────────────
        body = {"name": "Updated Test Hospital", "timezone": "IST", "date_format": "DD/MM/YYYY"}
        r = await c.patch(f"{BASE}/admin/settings/organization", headers=ah, json=body)
        log("admin_settings_update", "PATCH", "/admin/settings/organization", body, r.status_code, r.json())

        # ── ADMIN: ACCOUNTS ──────────────────────────────────────
        r = await c.get(f"{BASE}/admin/accounts", headers=ah)
        resp = r.json()[:2] if isinstance(r.json(), list) else r.json()
        log("admin_accounts", "GET", "/admin/accounts", None, r.status_code, resp)

        # ── AUDIT: LOGS ──────────────────────────────────────────
        r = await c.get(f"{BASE}/audit/logs?limit=3", headers=ah)
        log("audit_logs", "GET", "/audit/logs?limit=3", None, r.status_code, r.json())

        # ── AUDIT: STATS ─────────────────────────────────────────
        r = await c.get(f"{BASE}/audit/stats", headers=ah)
        log("audit_stats", "GET", "/audit/stats", None, r.status_code, r.json())

        # ── COMPLIANCE: MY DATA ──────────────────────────────────
        r = await c.get(f"{BASE}/compliance/my-data", headers=dh)
        resp = r.json()
        if isinstance(resp, dict): resp = {k: v for k, v in list(resp.items())[:4]}
        log("compliance_mydata", "GET", "/compliance/my-data", None, r.status_code, resp)

        # ── AUTH: LOGOUT ─────────────────────────────────────────
        r = await c.post(f"{BASE}/auth/logout", headers=dh)
        log("auth_logout", "POST", "/auth/logout", None, r.status_code, r.json() if r.text else {"message": "OK"})

    print("\n\n" + "="*60)
    print("CAPTURED RESULTS JSON:")
    print("="*60)
    print(json.dumps(RESULTS, indent=2, default=str))

asyncio.run(main())
