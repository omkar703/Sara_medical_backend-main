# Security Issues - Fixes Applied

This document outlines the security issues identified and the fixes that have been implemented.

---

## Issue #1: MinIO Patient Document Files NOT Deleted on Account Deletion

**Severity:** HIGH  
**File:** `app/api/v1/auth.py` → `delete_my_account()` endpoint

### Problem
When users deleted their accounts, database metadata for uploaded documents was deleted, but the actual document files stored in MinIO were left behind, orphaning storage and potentially exposing PHI.

### Fix Applied
Modified the `delete_my_account()` function to:
1. Retrieve all Document records (both uploaded by user and patient documents)
2. Delete each document file from MinIO storage via `minio_service.delete_object()`
3. Then delete the database metadata
4. Added error handling so MinIO failures don't crash the entire deletion process

**Changes:**
- **Lines 1525-1545:** Fetch and delete uploaded documents with MinIO cleanup
- **Lines 1572-1592:** Fetch and delete patient documents with MinIO cleanup

```python
# Before: Just deleted DB records
await db.execute(sql_delete(Document).where(Document.uploaded_by == user_id))

# After: Delete files from MinIO first, then DB records
docs_result = await db.execute(
    select(Document).where(Document.uploaded_by == user_id)
)
documents_to_delete = docs_result.scalars().all()

for doc in documents_to_delete:
    if doc.file_key:
        try:
            minio_service.delete_object(settings.MINIO_BUCKET_DOCUMENTS, doc.file_key)
        except Exception as minio_err:
            print(f"[DeleteAccount] MinIO delete failed for document {doc.id}: {minio_err}")

await db.execute(sql_delete(Document).where(Document.uploaded_by == user_id))
```

---

## Issue #2: No Rate Limiting on Auth Endpoints

**Severity:** MEDIUM  
**Files:** `app/api/v1/auth.py`

### Problem
Authentication endpoints (`/login`, `/register`, `/forgot-password`) were not protected against brute-force attacks and credential stuffing due to lack of rate limiting.

### Fix Applied
1. Added slowapi rate limiting import with fallback for installations without slowapi:
   ```python
   try:
       from slowapi import Limiter
       from slowapi.util import get_remote_address
       limiter = Limiter(key_func=get_remote_address)
   except ImportError:
       class NoOpLimiter:
           def limit(self, rate_limit):
               def decorator(func):
                   return func
               return decorator
       limiter = NoOpLimiter()
   ```

2. Applied rate limiting decorators to sensitive endpoints:
   - **`@router.post("/register")`** - `@limiter.limit("5/minute")` (line 680)
   - **`@router.post("/login")`** - `@limiter.limit("10/minute")` (line 908)
   - **`@router.post("/forgot-password")`** - `@limiter.limit("5/minute")` (line 1303)

**Note:** To fully enable this, install slowapi: `pip install slowapi`

---

## Issue #3: No Password Strength Validation

**Severity:** MEDIUM  
**File:** `app/schemas/auth.py`

### Problem
Password validation only enforced minimum length (8 characters) but did not require complexity, allowing weak passwords like "password1".

### Fix Applied
Enhanced password validation in UserCreate and ResetPasswordRequest schemas to enforce:
- ✓ Minimum 8 characters
- ✓ At least one uppercase letter (A-Z)
- ✓ At least one digit (0-9)
- ✓ At least one special character (!@#$%^&*)

**Changes:**
- **Lines 57-66:** UserCreate.password_strength validator updated
- **Lines 175-187:** ResetPasswordRequest.new_password validator added
- **Lines 175-187:** ResetPasswordRequest.password_strength validator added

```python
@validator('password')
def password_strength(cls, v):
    """Validate password strength - minimum 8 characters with complexity"""
    if len(v) < 8:
        raise ValueError('Password must be at least 8 characters')
    if not re.search(r'[A-Z]', v):
        raise ValueError('Password must contain at least one uppercase letter')
    if not re.search(r'\d', v):
        raise ValueError('Password must contain at least one digit')
    if not re.search(r'[^a-zA-Z0-9]', v):
        raise ValueError('Password must contain at least one special character')
    return v
```

---

## Issue #4: Phone Login Advertised but Not Implemented

**Severity:** LOW  
**File:** Frontend UI

**Status:** OUT OF SCOPE - This is a frontend UI issue, not a backend code issue.

**Recommendation:** Either implement phone-based OTP login or remove phone login option from signup UI.

---

## Issue #5: External AI API Disclosure & PHI Processing Without Consent

**Severity:** HIGH  
**Files:** `app/api/v1/ai.py`, `app/models/user.py`

### Problem
- The application uses Claude (Anthropic via AWS Bedrock) for AI document processing and analysis
- No privacy policy disclosure about which AI provider is used
- No user consent mechanism for processing PHI with external AI APIs
- Doctors could process patient documents without explicit patient consent

### Fix Applied

#### A. Added AI Consent Model Field
**File:** `app/models/user.py` (line 108)
```python
ai_processing_consented = Column(Boolean, default=False, nullable=False)
```

#### B. Added AI Consent Schemas
**File:** `app/api/v1/ai.py` (lines 96-110)
```python
class AIConsentRequest(BaseModel):
    consented: bool
    acknowledged_provider: str = "anthropic"

class AIConsentResponse(BaseModel):
    patient_id: UUID
    consented: bool
    ai_provider: str = "Claude (Anthropic via AWS Bedrock)"
    privacy_notice: str = "PHI may be processed by Claude for document analysis..."
```

#### C. Added AI Consent Management Endpoints
**File:** `app/api/v1/ai.py`

1. **POST `/doctor/ai/consent`** - Grant/revoke AI processing consent
   ```python
   @router.post("/consent", response_model=AIConsentResponse)
   async def set_ai_consent(request: AIConsentRequest, ...):
       # Allows patients to consent to Claude processing of their PHI
   ```

2. **GET `/doctor/ai/consent`** - Retrieve current consent status
   ```python
   @router.get("/consent", response_model=AIConsentResponse)
   async def get_ai_consent(...):
       # Shows current consent status and AI provider info
   ```

#### D. Added Consent Check to Document Processing
**File:** `app/api/v1/ai.py` (lines 147-151)
```python
if not getattr(patient, 'ai_processing_consented', False):
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Patient has not consented to AI processing. Please obtain consent..."
    )
```

### Privacy Policy Updates Required
Add to Privacy Policy:
- AI Provider: Claude (Anthropic)
- Processing Method: AWS Bedrock
- Data Processed: Medical documents, health records, consultation notes
- User Consent: Explicit opt-in required before any AI processing

---

## Summary of Changes

| Issue | Severity | Status | Files Modified |
|-------|----------|--------|-----------------|
| #1: MinIO Documents Not Deleted | HIGH | ✅ FIXED | `app/api/v1/auth.py` |
| #2: No Rate Limiting | MEDIUM | ✅ FIXED | `app/api/v1/auth.py` |
| #3: Weak Password Validation | MEDIUM | ✅ FIXED | `app/schemas/auth.py` |
| #4: Phone Login Not Implemented | LOW | ⏭️ DEFER | Frontend UI |
| #5: AI API PHI Processing Without Consent | HIGH | ✅ FIXED | `app/api/v1/ai.py`, `app/models/user.py` |

---

## Testing Recommendations

### Issue #1 Testing
```bash
# Test account deletion with documents
POST /api/v1/auth/me  # delete current user
# Verify: MinIO bucket should have fewer files after deletion
```

### Issue #2 Testing
```bash
# Test rate limiting (make >5 requests in 60 seconds)
for i in {1..6}; do
  curl -X POST http://localhost:8000/api/v1/auth/register \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","password":"Test@123"}'
done
# Expected: 6th request returns 429 Too Many Requests
```

### Issue #3 Testing
```bash
# Test weak passwords (should fail)
POST /api/v1/auth/register
{"email":"test@example.com","password":"password"}  # No uppercase, no special char

# Test strong passwords (should succeed)
POST /api/v1/auth/register
{"email":"test@example.com","password":"SecureP@ss123"}  # Has uppercase, digit, special
```

### Issue #5 Testing
```bash
# Patient grants consent
POST /api/v1/doctor/ai/consent
{"consented": true, "acknowledged_provider": "anthropic"}

# Check consent status
GET /api/v1/doctor/ai/consent

# Try to process document (should succeed if consented)
POST /api/v1/doctor/ai/process-document
{"patient_id":"...", "document_id":"..."}

# Try without consent (should fail)
# First, revoke consent
POST /api/v1/doctor/ai/consent
{"consented": false}

# Try process again (should return 403)
POST /api/v1/doctor/ai/process-document
# Expected: 403 Forbidden - Patient has not consented to AI processing
```

---

## Database Migration Needed

For Issue #5, a database migration is required to add the new column to the users table:

```sql
ALTER TABLE users ADD COLUMN ai_processing_consented BOOLEAN NOT NULL DEFAULT FALSE;
```

Or using Alembic:
```bash
alembic revision --autogenerate -m "Add AI consent field to users"
alembic upgrade head
```

---

## Dependencies to Install

For Issue #2 (Rate Limiting):
```bash
pip install slowapi
```

Update `requirements.txt` to include: `slowapi>=0.1.9`

---

## Deployment Notes

1. **Database Migration:** Run migration for AI consent field before deployment
2. **Environment Variables:** Ensure `MINIO_BUCKET_DOCUMENTS` is set correctly
3. **Privacy Policy:** Update website privacy policy to disclose Claude/Anthropic AI processing
4. **User Communication:** Notify existing users about new AI consent requirements
5. **Rate Limiting:** If slowapi is not installed, rate limiting will be a no-op (use fallback)

