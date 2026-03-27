# Apple Auth Quick Reference

## Quick Start Checklist

- [ ] Get Apple Team ID from [developer.apple.com/account](https://developer.apple.com/account)
- [ ] Create Service ID at [developer.apple.com/account/resources/identifiers](https://developer.apple.com/account/resources/identifiers/list)
- [ ] Create Private Key at [developer.apple.com/account/resources/authkeys](https://developer.apple.com/account/resources/authkeys/list)
- [ ] Configure Web Authentication domains and redirect URIs in Service ID settings
- [ ] Add environment variables to `.env` file
- [ ] Test `/api/v1/auth/apple/login` endpoint
- [ ] Integrate Apple Sign In button on frontend
- [ ] Test complete flow in staging environment

---

## File Structure

```
app/
├── api/v1/
│   └── auth.py                 # Apple auth endpoints here
├── config.py                   # Apple config variables
├── models/
│   └── user.py                 # apple_id field in User model
└── core/
    └── security.py             # JWT and token handling

Root files:
├── APPLE_AUTH_SETUP.md         # Complete setup guide
├── APPLE_AUTH_ENV_EXAMPLE.md   # Environment variables example
├── APPLE_AUTH_QUICK_REF.md     # This file
└── test_apple_auth.py          # Tests
```

---

## Environment Variables

```bash
APPLE_TEAM_ID=XXXXXXXXXX
APPLE_CLIENT_ID=com.yourcompany.app.service
APPLE_KEY_ID=YYYYYYYYYY
APPLE_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----
APPLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/apple/callback
```

---

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/v1/auth/apple/login` | Initiate Apple Sign In |
| POST | `/api/v1/auth/apple/callback` | Handle Apple callback |

---

## Response Structure

### Success Response (Redirect with Tokens)
```
https://frontend.com/auth/apple/callback
?access_token=<JWT>
&refresh_token=<JWT>
&user={"id":"...","email":"...","role":"..."}
```

### Error Response (Redirect with Error)
```
https://frontend.com/auth/apple/callback
?error=Account%20not%20found
```

---

## Key Files Modified

1. **app/config.py**
   - Added: `APPLE_TEAM_ID`, `APPLE_KEY_ID`, `APPLE_PRIVATE_KEY` config variables
   - Already had: `APPLE_CLIENT_ID`, `APPLE_REDIRECT_URI`

2. **app/api/v1/auth.py**
   - Added: `AppleSignInHelper` class for token generation and verification
   - Added: `@router.get("/apple/login")` endpoint
   - Added: `@router.post("/apple/callback")` endpoint
   - Uses existing: token generation, user lookup, refresh token creation

3. **New files created**
   - `APPLE_AUTH_SETUP.md` - Complete setup documentation
   - `APPLE_AUTH_ENV_EXAMPLE.md` - Environment variables guide
   - `test_apple_auth.py` - Test suite

---

## Implementation Details

### AppleSignInHelper Class

Handles Apple-specific authentication logic:

```python
class AppleSignInHelper:
    @staticmethod
    def generate_client_secret() -> str:
        # Generates JWT client secret for Apple API calls
        # Uses APPLE_TEAM_ID, APPLE_KEY_ID, APPLE_PRIVATE_KEY
    
    @staticmethod
    async def verify_id_token(token: str) -> dict:
        # Decodes and verifies Apple ID token
        # Returns user info (email, apple_id, etc.)
```

### Login Flow

```
1. Frontend: User clicks "Sign in with Apple"
   ↓
2. POST /api/v1/auth/apple/login
   ↓
3. Backend: Redirects to Apple OAuth page
   ↓
4. Apple: User authenticates
   ↓
5. Apple: POST to /api/v1/auth/apple/callback
   ↓
6. Backend: Verifies token, links user, generates JWT
   ↓
7. Backend: Redirects to frontend with tokens
   ↓
8. Frontend: Stores tokens, redirects to dashboard
```

---

## Database

### User Model Changes

```python
class User(Base):
    # Existing fields...
    
    # Social Auth
    google_id: Optional[str]    # Existing
    apple_id: Optional[str]     # Added in migration
```

### Migration Applied

File: `alembic/versions/20260208_1543_7e27fda403a5_ensure_social_auth_columns.py`
- Added `apple_id` column to `users` table
- Created unique index on `apple_id`

---

## Testing

### Manual Testing

```bash
# 1. Check configuration
curl -X GET http://localhost:8000/api/v1/auth/apple/login

# 2. Should redirect to Apple's OAuth page
# 3. Can also test in browser by visiting the URL directly
```

### Automated Testing

```bash
# Run test suite
pytest test_apple_auth.py -v

# Run specific test
pytest test_apple_auth.py::TestAppleLoginEndpoint -v
```

---

## Frontend Integration Example

```javascript
// React example
import { useEffect } from 'react';

export function AppleAuthCallback() {
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get('access_token');
    const error = params.get('error');
    
    if (error) {
      console.error('Apple Auth Error:', error);
      window.location.href = '/login?error=' + error;
      return;
    }
    
    if (token) {
      // Store token
      localStorage.setItem('access_token', token);
      localStorage.setItem('refresh_token', params.get('refresh_token'));
      
      // Redirect to dashboard
      window.location.href = '/dashboard';
    }
  }, []);

  return <div>Signing in...</div>;
}
```

---

## Differences from Google Auth

| Feature | Google | Apple |
|---------|--------|-------|
| **SSO Library** | fastapi-sso | Custom (jose JWT) |
| **Credentials** | Client ID + Secret | Team ID + Key ID + Private Key |
| **Token Type** | OAuth token | JWT |
| **Email Privacy** | Direct email | May use private relay |
| **Callback Method** | GET redirect | POST form-encoded |
| **User ID** | Consistent | Changes per app |

---

## Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| "Apple Auth not configured" | Missing env vars | Set all APPLE_* variables |
| Blank page at callback | Frontend URL missing | Add `/auth/apple/callback` route |
| "Invalid redirect URI" | URI mismatch | Check exact spelling in Apple console |
| Account not found | User not registered | Admin must create user first |
| Private relay email | User chose "Hide My Email" | System handles automatically |

---

## Security Checklist

- [ ] Private key not in git/version control
- [ ] Environment variables set securely
- [ ] HTTPS used in production
- [ ] Token verification enabled (for production)
- [ ] Redirect URIs whitelisted in Apple console
- [ ] Rate limiting on auth endpoints
- [ ] Logging for auth events
- [ ] Regular key rotation (yearly)

---

## Links

- [Apple Sign In Docs](https://developer.apple.com/sign-in-with-apple/)
- [Apple Developer Console](https://developer.apple.com/account)
- [JWT Guide](https://jwt.io)
- [FastAPI Docs](https://fastapi.tiangolo.com)
- [Python-Jose](https://github.com/mpdavis/python-jose)

---

## Support

For detailed setup instructions, see: `APPLE_AUTH_SETUP.md`
For environment examples, see: `APPLE_AUTH_ENV_EXAMPLE.md`
For tests, see: `test_apple_auth.py`
