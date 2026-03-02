"""
RAG Endpoint Tester — tests the actual live API endpoints
Covers:
  STEP 1  Login as doctor → get JWT token
  STEP 2  POST /api/v1/doctor/ai/chat/doctor (RAG chat with patient data)
  STEP 3  GET  /api/v1/doctor/ai/chat-history/doctor (fetch chat history)

Run: python test_rag_endpoint.py

Requirements:
  - Backend server must be running (docker-compose up OR uvicorn app.main:app)
  - Update BASE_URL, DOCTOR_EMAIL, DOCTOR_PASSWORD, PATIENT_ID below
"""

import asyncio
import httpx
import json
import sys
import time
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# ── CONFIG — update these ───────────────────────────────────────────────────
BASE_URL      = "http://localhost:8000"      # change if running on different port
DOCTOR_EMAIL  = os.getenv("TEST_DOCTOR_EMAIL",   "doctor@example.com")
DOCTOR_PASS   = os.getenv("TEST_DOCTOR_PASSWORD", "Test@1234")
PATIENT_ID    = os.getenv("TEST_PATIENT_ID",      "")   # UUID of patient with documents
DOCUMENT_ID   = os.getenv("TEST_DOCUMENT_ID",     "")   # optional: specific document UUID
ORG_ID        = os.getenv("TEST_ORG_ID",          "")   # UUID of the organisation

# Test queries to send to the RAG endpoint
TEST_QUERIES = [
    "What are the patient's current medications?",
    "What is the latest HbA1c result and what does it indicate?",
    "Summarise the patient's recent diagnosis and treatment plan.",
]

TIMEOUT = 60  # seconds

# ── Colours ─────────────────────────────────────────────────────────────────
def ok(s):    print(f"  \033[92m✅ {s}\033[0m")
def fail(s):  print(f"  \033[91m❌ {s}\033[0m")
def info(s):  print(f"  \033[96mℹ  {s}\033[0m")
def warn(s):  print(f"  \033[93m⚠  {s}\033[0m")
def dim(s):   print(f"  \033[90m   {s}\033[0m")
def step(n, t, s): 
    print(f"\n\033[1m\033[94m[STEP {n}/{t}]\033[0m {s}")
    print("  " + "─" * 55)


# ── Helpers ──────────────────────────────────────────────────────────────────
def check_config():
    print("\n\033[1m🔧 Configuration\033[0m")
    print("─" * 50)
    print(f"  BASE_URL     : {BASE_URL}")
    print(f"  DOCTOR_EMAIL : {DOCTOR_EMAIL}")
    print(f"  PATIENT_ID   : {PATIENT_ID or '⚠ NOT SET'}")
    print(f"  DOCUMENT_ID  : {DOCUMENT_ID or '(none — will search all docs)'}")
    print(f"  ORG_ID       : {ORG_ID or '⚠ NOT SET'}")

    missing = []
    if not PATIENT_ID:
        missing.append("TEST_PATIENT_ID")
    if not ORG_ID:
        missing.append("TEST_ORG_ID")

    if missing:
        warn(f"Missing env vars: {', '.join(missing)}")
        warn("Add them to .env or set below in this script.")
        warn("You can find these IDs from the DB or the /patients API.")
        print()


async def check_server(client: httpx.AsyncClient) -> bool:
    """Ping the server health endpoint."""
    try:
        r = await client.get(f"{BASE_URL}/health", timeout=5)
        return r.status_code == 200
    except Exception:
        return False


# ── STEP 1: Login ────────────────────────────────────────────────────────────
async def login(client: httpx.AsyncClient) -> str | None:
    step(1, 3, "Authenticate — POST /api/v1/auth/login")

    payload = {"email": DOCTOR_EMAIL, "password": DOCTOR_PASS}
    info(f"Email    : {DOCTOR_EMAIL}")
    info(f"Endpoint : POST {BASE_URL}/api/v1/auth/login")

    try:
        t0 = time.time()
        r = await client.post(
            f"{BASE_URL}/api/v1/auth/login",
            json=payload,
            timeout=TIMEOUT,
        )
        elapsed = time.time() - t0

        if r.status_code == 200:
            data = r.json()
            token = data.get("access_token") or data.get("token")
            if token:
                ok(f"Login successful ({elapsed:.2f}s)")
                dim(f"Token: {token[:30]}...{token[-10:]}")
                user = data.get("user", {})
                if user:
                    info(f"User  : {user.get('email','?')}  role={user.get('role','?')}")
                return token
            else:
                fail(f"Login OK but no token in response: {list(data.keys())}")
        else:
            fail(f"HTTP {r.status_code}: {r.text[:200]}")

    except httpx.ConnectError:
        fail(f"Cannot connect to {BASE_URL} — is the server running?")
    except Exception as e:
        fail(f"Login error: {e}")

    return None


# ── STEP 2: RAG Chat ─────────────────────────────────────────────────────────
async def test_rag_chat(client: httpx.AsyncClient, token: str):
    step(2, 3, "RAG Chat — POST /api/v1/doctor/ai/chat/doctor")

    if not PATIENT_ID:
        warn("PATIENT_ID not set — skipping chat test")
        warn("Set TEST_PATIENT_ID in .env or in this script")
        return None

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": ORG_ID,
        "Content-Type": "application/json",
    }

    last_response = None

    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"\n  \033[1mQuery {i}/{len(TEST_QUERIES)}\033[0m: \033[96m{query}\033[0m")

        payload = {
            "patient_id": PATIENT_ID,
            "query": query,
        }
        if DOCUMENT_ID:
            payload["document_id"] = DOCUMENT_ID

        try:
            t0 = time.time()
            r = await client.post(
                f"{BASE_URL}/api/v1/doctor/ai/chat/doctor",
                headers=headers,
                json=payload,
                timeout=TIMEOUT,
            )
            elapsed = time.time() - t0

            if r.status_code == 200:
                # Response may be streaming (text/event-stream) or plain JSON
                content_type = r.headers.get("content-type", "")
                response_text = r.text.strip()

                ok(f"HTTP 200 ({elapsed:.2f}s)  content-type: {content_type}")

                if response_text:
                    last_response = response_text
                    preview = response_text[:300]
                    print()
                    print("  \033[1mResponse:\033[0m")
                    for line in preview.split("\n"):
                        dim(line)
                    if len(response_text) > 300:
                        dim(f"... ({len(response_text)} chars total)")
                else:
                    warn("Response body is empty")

            elif r.status_code == 404:
                fail(f"HTTP 404 — No documents found for patient (chunks table may be empty)")
                info("Upload and process a document first via POST /api/v1/documents")

            elif r.status_code == 403:
                fail(f"HTTP 403 — Permission denied: {r.text[:150]}")
                info("Doctor may not have access to this patient's data")
                info("Use POST /api/v1/permissions to grant access")

            elif r.status_code == 401:
                fail("HTTP 401 — Token expired or invalid")

            else:
                fail(f"HTTP {r.status_code}: {r.text[:200]}")

        except httpx.ReadTimeout:
            warn(f"Request timed out after {TIMEOUT}s — LLM may still be processing")
        except Exception as e:
            fail(f"Request error: {e}")

    return last_response


# ── STEP 3: Chat History ─────────────────────────────────────────────────────
async def test_chat_history(client: httpx.AsyncClient, token: str):
    step(3, 3, "Chat History — GET /api/v1/doctor/ai/chat-history/doctor")

    if not PATIENT_ID:
        warn("PATIENT_ID not set — skipping history test")
        return

    # Decode the doctor user ID from the token (or derive from login)
    # We'll just call with the current user's token and require doctor_id param
    # Attempt to decode JWT to get sub (user id)
    try:
        import base64, json as _json
        parts = token.split(".")
        padded = parts[1] + "=" * (4 - len(parts[1]) % 4)
        payload_data = _json.loads(base64.urlsafe_b64decode(padded))
        doctor_id = payload_data.get("sub") or payload_data.get("user_id") or ""
        dim(f"Doctor ID from JWT: {doctor_id}")
    except Exception:
        doctor_id = ""
        warn("Could not decode JWT to get doctor_id — set TEST_DOCTOR_ID in .env")

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": ORG_ID,
    }

    params = {"patient_id": PATIENT_ID, "doctor_id": doctor_id}
    info(f"patient_id : {PATIENT_ID}")
    info(f"doctor_id  : {doctor_id or '(not resolved)'}")

    try:
        t0 = time.time()
        r = await client.get(
            f"{BASE_URL}/api/v1/doctor/ai/chat-history/doctor",
            headers=headers,
            params=params,
            timeout=30,
        )
        elapsed = time.time() - t0

        if r.status_code == 200:
            data = r.json()
            history = data.get("history", [])
            ok(f"HTTP 200 ({elapsed:.2f}s) — {len(history)} messages in history")
            for msg in history[:3]:
                role = msg.get("role", "?")
                content = str(msg.get("content", ""))[:100]
                dim(f"[{role.upper()}]: {content}...")
            if len(history) > 3:
                dim(f"... and {len(history) - 3} more messages")
        else:
            fail(f"HTTP {r.status_code}: {r.text[:200]}")

    except Exception as e:
        fail(f"History request error: {e}")


# ── Main ─────────────────────────────────────────────────────────────────────
async def main():
    print("═" * 60)
    print("\033[1m  RAG Endpoint Test — Sara Medical Backend\033[0m")
    print("═" * 60)

    check_config()

    async with httpx.AsyncClient() as client:
        # Health check
        print("\n\033[1m🏥 Server Health Check\033[0m")
        print("─" * 50)
        alive = await check_server(client)
        if alive:
            ok(f"Server is up at {BASE_URL}")
        else:
            fail(f"Server not reachable at {BASE_URL}")
            print()
            warn("Start the server first:")
            print("    docker-compose up")
            print("    OR")
            print("    uvicorn app.main:app --reload --port 8000")
            sys.exit(1)

        # Run steps
        token = await login(client)
        if not token:
            fail("Cannot proceed without a valid token")
            sys.exit(1)

        await test_rag_chat(client, token)
        await test_chat_history(client, token)

    # Summary
    print("\n" + "═" * 60)
    print("\033[1m  Test Complete\033[0m")
    print("═" * 60)
    print()
    if not PATIENT_ID:
        warn("RAG chat was skipped — set TEST_PATIENT_ID in .env")
        print()
        info("Quick setup: add these to your .env and re-run:")
        print("    TEST_DOCTOR_EMAIL=doctor@yourdomain.com")
        print("    TEST_DOCTOR_PASSWORD=yourpassword")
        print("    TEST_PATIENT_ID=<patient-uuid>")
        print("    TEST_ORG_ID=<organization-uuid>")
        print()
    print("═" * 60)


if __name__ == "__main__":
    asyncio.run(main())
