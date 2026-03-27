# Apple Sign In Authentication Setup Guide

This guide provides step-by-step instructions to set up Apple Sign In authentication for the Saramedico backend.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Apple Developer Setup](#apple-developer-setup)
3. [Configuration](#configuration)
4. [API Endpoints](#api-endpoints)
5. [Frontend Integration](#frontend-integration)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before starting, ensure you have:
- An Apple Developer Account (paid membership required for production)
- Access to [Apple Developer Console](https://developer.apple.com/account)
- Backend URL (for redirect URI)
- Frontend URL (for callback handling)

---

## Apple Developer Setup

### Step 1: Create an App ID

1. Go to [Certificates, IDs & Profiles](https://developer.apple.com/account/resources/identifiers/list)
2. Click **"Identifiers"** → **"App IDs"**
3. Click the **"+"** button to create a new App ID
4. Choose **"App IDs"** and click **"Continue"**
5. Select **"App"** and click **"Continue"**
6. Fill in:
   - **Description**: e.g., "Saramedico Web App"
   - **Bundle ID**: Use a reverse domain name, e.g., `com.saramedico.web`
7. Scroll down and check **"Sign in with Apple"**
8. Click **"Continue"** and then **"Register"**

### Step 2: Enable "Sign in with Apple" for Web

1. Open the App ID you just created
2. Under **"Capabilities"**, find **"Sign in with Apple"**
3. Click **"Configure"**
4. Add your web domain:
   - **Domain**: Your backend domain (e.g., `api.saramedico.com`)
   - **Return URLs**: Your callback URL (e.g., `https://api.saramedico.com/api/v1/auth/apple/callback`)
5. Click **"Save"**

### Step 3: Create a Service ID

1. Go to **Identifiers** → **Service IDs**
2. Click the **"+"** button
3. Choose **"Service IDs"** and click **"Continue"**
4. Fill in:
   - **Description**: e.g., "Saramedico Web Service"
   - **Identifier**: This is your `APPLE_CLIENT_ID` - use format like `com.saramedico.web.service`
5. Check **"Sign in with Apple"**
6. Click **"Configure"**
7. Under **"Web Authentication Configuration**:
   - **Domains and Subdomains**: Add your backend domain
   - **Return URLs**: Add your callback URL(s)
   - Example: `https://api.saramedico.com/api/v1/auth/apple/callback`
8. Click **"Save"** → **"Continue"** → **"Register"**

### Step 4: Create a Private Key

1. Go to **Keys** (under Certificates, IDs & Profiles)
2. Click the **"+"** button
3. Choose **"App IDs"** and click **"Continue"**
4. Enter a **Key Name**: e.g., "Saramedico Web Key"
5. Check **"Sign in with Apple"**
6. Click **"Continue"** → **"Register"**
7. **Download** the private key (`.p8` file)
8. **Important**: Save this file securely - you can only download it once!

From this key, you'll need:
- **Key ID**: Shown in the Apple Developer console (10 characters)
- **Private Key**: Content of the `.p8` file
- **Team ID**: Your Apple Developer Team ID (10 characters, found in Account Settings)

---

## Configuration

### Step 1: Add Environment Variables

Create or update your `.env` file with:

```bash
# Apple Authentication
APPLE_CLIENT_ID=com.saramedico.web.service
APPLE_TEAM_ID=XXXXXXXXXX
APPLE_KEY_ID=XXXXXXXXXX
APPLE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nMIGTAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgQ7PvDhVmAV7tQ9vU\n...\n-----END PRIVATE KEY-----"
APPLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/apple/callback
```

**Important Notes**:
- For the `APPLE_PRIVATE_KEY`, replace all newlines with `\n` (literal backslash-n)
- In production, use `https://` for the redirect URI
- Keep the private key secure - never commit to version control

### Step 2: Local Development Setup

For local development with Docker or local server:

```bash
APPLE_CLIENT_ID=com.saramedico.web.service
APPLE_TEAM_ID=XXXXXXXXXX
APPLE_KEY_ID=XXXXXXXXXX
APPLE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----"
APPLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/apple/callback
```

### Step 3: Production Setup

For production:

```bash
APPLE_CLIENT_ID=com.saramedico.web.service
APPLE_TEAM_ID=XXXXXXXXXX
APPLE_KEY_ID=XXXXXXXXXX
APPLE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----"
APPLE_REDIRECT_URI=https://api.saramedico.com/api/v1/auth/apple/callback
```

---

## API Endpoints

### 1. Initiate Apple Sign In

**Endpoint**: `GET /api/v1/auth/apple/login`

**Description**: Redirects the user to Apple's OAuth login page.

**Response**: Redirect to Apple's authorization URL

**Example**:
```bash
curl -X GET http://localhost:8000/api/v1/auth/apple/login
```

### 2. Handle Apple Callback

**Endpoint**: `POST /api/v1/auth/apple/callback`

**Description**: Handles the callback from Apple after user authorizes the app.

**Request Body** (form-encoded, sent by Apple):
```
id_token=<JWT_TOKEN>
user=<USER_ID>
```

**Response**: Redirect to frontend callback with tokens

**Query Parameters**:
- `access_token`: JWT access token for API authentication
- `refresh_token`: Refresh token for getting new access tokens
- `user`: JSON object with user information
- `error` (on failure): Error message

**Example Frontend Callback URL**:
```
https://saramedico-deploy.vercel.app/auth/apple/callback
?access_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
&refresh_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
&user={"id":"123","email":"user@example.com",...}
```

---

## Frontend Integration

### 1. Create Apple Sign In Button

```html
<!-- Using native Apple Sign In button -->
<script
  type="text/javascript"
  src="https://appleid.cdn-apple.com/js/appleid.js"
  defer
></script>

<div
  id="appleid-signin"
  data-type="sign-in"
  data-mode="black"
  data-locale="en_US"
  data-size="200"
  data-theme="black"
  data-border="true"
  data-border-radius="12"
  data-scale="1.2"
></div>
```

### 2. Handle Apple Sign In

```javascript
// Configure Apple Sign In
window.AppleID.auth.init({
  clientId: process.env.REACT_APP_APPLE_CLIENT_ID,
  teamId: process.env.REACT_APP_APPLE_TEAM_ID,
  keyId: process.env.REACT_APP_APPLE_KEY_ID,
  redirectUri: window.location.origin + '/auth/apple/callback',
  scope: 'email name',
  redirectMethod: 'POST', // Use POST for the redirect
  usePopup: true, // Use popup instead of redirect
});

// Listen for sign-in events
window.AppleID.auth.onCredentialResponse(async (data) => {
  // Handle successful sign-in
  const response = await fetch(
    `${API_BASE}/auth/apple/callback`,
    {
      method: 'POST',
      body: data.authorization.id_token,
    }
  );
  const result = await response.json();
  // Store tokens and redirect to dashboard
  localStorage.setItem('access_token', result.access_token);
  localStorage.setItem('refresh_token', result.refresh_token);
  window.location.href = '/dashboard';
});
```

### 3. Handle Callback Route

```javascript
import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

export function AppleAuthCallback() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  useEffect(() => {
    const accessToken = searchParams.get('access_token');
    const refreshToken = searchParams.get('refresh_token');
    const userStr = searchParams.get('user');
    const error = searchParams.get('error');

    if (error) {
      console.error('Apple Auth Error:', error);
      navigate('/login?error=' + error);
      return;
    }

    if (accessToken && refreshToken && userStr) {
      // Store tokens
      localStorage.setItem('access_token', accessToken);
      localStorage.setItem('refresh_token', refreshToken);
      
      // Parse and store user info
      const user = JSON.parse(decodeURIComponent(userStr));
      localStorage.setItem('user', JSON.stringify(user));

      // Redirect to dashboard
      navigate('/dashboard');
    }
  }, [searchParams, navigate]);

  return <div>Processing Apple Sign In...</div>;
}
```

---

## Testing

### Manual Testing

1. **Test Login Flow**:
   ```bash
   curl -X GET http://localhost:8000/api/v1/auth/apple/login
   ```

2. **Verify Configuration**:
   - Check that all environment variables are set correctly
   - Verify the redirect URI matches in Apple Developer console

3. **Test with Browser**:
   - Click the Apple Sign In button
   - Complete the Apple authentication flow
   - Check if redirect to frontend callback works

### Automated Testing

See `test_apple_auth.py` in the repository for automated tests.

```bash
# Run Apple auth tests
pytest test_apple_auth.py -v
```

---

## Troubleshooting

### Error: "Apple Auth not configured"

**Cause**: Environment variables not set.

**Solution**:
1. Verify all required variables are in `.env`:
   - `APPLE_CLIENT_ID`
   - `APPLE_TEAM_ID`
   - `APPLE_KEY_ID`
   - `APPLE_PRIVATE_KEY`
2. Restart the backend server

### Error: "Invalid Apple ID token"

**Cause**: Token is expired or malformed.

**Solution**:
1. Ensure the ID token is fresh (Apple issues them for the current session)
2. Check token format - should be a valid JWT
3. Verify private key is correct

### Error: "Account not found"

**Cause**: User's email doesn't exist in the system.

**Solution**:
1. User must be registered by an admin/provider before using Apple Sign In
2. Email used in Apple ID must match the registered email

### Apple Sign In Button Not Appearing

**Cause**: Apple SDK not loaded or domain not configured.

**Solution**:
1. Verify domain is added in Apple Developer console
2. Check browser console for CORS errors
3. Ensure `appleid.cdn-apple.com/js/appleid.js` is loaded

### Redirect Loop or Blank Page

**Cause**: Redirect URI mismatch.

**Solution**:
1. Verify `APPLE_REDIRECT_URI` matches exactly in Apple Developer console
2. For development: `http://localhost:8000/api/v1/auth/apple/callback`
3. For production: `https://api.saramedico.com/api/v1/auth/apple/callback`
4. Check frontend callback URL matches in React router

### Email Privacy Issue

**Cause**: User selected "Hide My Email" in Apple Sign In.

**Solution**:
Apple will provide a private relay email (`*.privaterelay@applemail.com`). The backend handles this automatically:
- Stores the private relay email on first login
- User can still authenticate with the same Apple ID
- In future logins, user info is linked via `apple_id` field

---

## Security Considerations

1. **Private Key Security**:
   - Never commit the private key to version control
   - Use environment variables or secure key management systems
   - Rotate keys periodically

2. **Token Verification**:
   - Always verify JWT tokens from Apple
   - Check token expiration
   - Validate token signature (currently disabled for development, enable in production)

3. **HTTPS Requirements**:
   - Production redirect URIs must use HTTPS
   - Development can use HTTP for testing

4. **Email Verification**:
   - Apple provides verified emails - trust their verification
   - Backend automatically marks `email_verified = True` after Apple auth

---

## API Reference

### User Model Fields

After successful Apple authentication, the user record includes:

```python
{
    "id": UUID,
    "email": str,
    "apple_id": str,  # Apple's unique user identifier
    "email_verified": bool,  # Set to True after Apple auth
    "last_login": datetime,
    "created_at": datetime,
    "updated_at": datetime,
    # ... other fields
}
```

### Response Tokens

Both tokens are JWTs with the following structure:

**Access Token** (valid for 24 hours):
```python
{
    "sub": user_id,      # User ID
    "role": user_role,   # doctor, patient, admin, etc.
    "iat": issued_at,    # Issued at
    "exp": expires_at    # Expires at
}
```

**Refresh Token** (valid for 30 days):
```python
{
    "sub": user_id,
    "type": "refresh",
    "iat": issued_at,
    "exp": expires_at
}
```

---

## Additional Resources

- [Apple Sign In Documentation](https://developer.apple.com/sign-in-with-apple/)
- [Apple ID Authentication Services](https://developer.apple.com/documentation/authenticationservices)
- [JWT Verification Guide](https://developer.apple.com/documentation/sign_in_with_apple/fetch_apple_s_public_key_for_verifying_token_signature)

---

## Support

For issues or questions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review Apple Developer documentation
3. Check backend logs: `logs/saramedico.log`
4. Contact the development team
