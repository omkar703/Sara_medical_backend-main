# 🔧 Real Google Meet Integration Setup Guide

## Problem Fixed ✅

Previously, consultations were generating **invalid mock links** like:
```
https://meet.google.com/mock-8830-ecf7
```

This has been fixed! The system now requires **real Google Meet credentials** to generate valid meeting links.

---

## What Changed

### Code Updates

1. **`app/services/consultation_service.py`**
   - Removed mock Google Meet fallback
   - Now requires real Google credentials
   - Fails explicitly with helpful error message if credentials are missing

2. **`app/api/v1/appointments.py`**
   - Updated to use real Google Meet service only
   - Removed mock generation logic
   - Consistent error handling for credential issues

### Result

When you schedule a consultation, you'll now get **real Google Meet links** like:
```
https://meet.google.com/abc-defg-hij-klm
```

---

## 🚀 Setup Instructions

### Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a Project" → "New Project"
3. Name it: `Saramedico` (or your preferred name)
4. Click "Create"

### Step 2: Enable Google Calendar API

1. In your project, go to **APIs & Services** → **Library**
2. Search for **"Google Calendar API"**
3. Click on it
4. Click the **"Enable"** button

### Step 3: Create OAuth 2.0 Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **"Create Credentials"** → **"OAuth client ID"**
3. You might see a warning to "Configure the OAuth consent screen first" — click that link
4. On the consent screen:
   - Choose **"External"** for User Type
   - Fill in App name: `Saramedico`
   - Add your email as a test user
   - Save and continue
5. Back to Credentials, click **"Create Credentials"** → **"OAuth client ID"** again
6. Choose **"Desktop application"**
7. Click **"Create"**
8. A JSON file will be shown. Copy:
   - `client_id` → This is your `GOOGLE_CLIENT_ID`
   - `client_secret` → This is your `GOOGLE_CLIENT_SECRET`

### Step 4: Generate Refresh Token

Run this Python script to generate the refresh token:

```python
from google_auth_oauthlib.flow import InstalledAppFlow
import json

# Replace these with values from Step 3
CLIENT_ID = "your-client-id.apps.googleusercontent.com"
CLIENT_SECRET = "your-client-secret"

SCOPES = [
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/drive.readonly'
]

# Create a flow manually
from google.oauth2.client_config import ClientConfig

config = {
    "type": "desktop",
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "redirect_uris": ["http://localhost"]
}

flow = InstalledAppFlow.from_client_config(
    {"installed": config},
    SCOPES
)

creds = flow.run_local_server(port=8080)

print(f"\n✅ SUCCESS! Copy these to your .env file:\n")
print(f"GOOGLE_CLIENT_ID={CLIENT_ID}")
print(f"GOOGLE_CLIENT_SECRET={CLIENT_SECRET}")
print(f"GOOGLE_REFRESH_TOKEN={creds.refresh_token}")
```

**Or simplify using the downloaded JSON:**

```python
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/drive.readonly'
]

# Use your downloaded client_secret.json from Step 3
flow = InstalledAppFlow.from_client_secrets_file(
    'client_secret.json',  # Your downloaded file
    SCOPES
)

creds = flow.run_local_server(port=8080)
print(f"GOOGLE_REFRESH_TOKEN={creds.refresh_token}")
```

### Step 5: Update Your `.env` File

Add the following to your `.env` file:

```env
# Google Meet Configuration
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REFRESH_TOKEN=your-refresh-token

# Enable real video calls
FEATURE_VIDEO_CALLS=true
```

**Find your `.env` file location:**
```bash
# In the project root:
ls -la .env

# If it doesn't exist, create it from the example:
cp .env.example .env
```

### Step 6: Restart Your Backend

```bash
# If running locally with uvicorn:
# (Stop the current process with Ctrl+C)
python -m uvicorn app.main:app --reload

# If using Docker:
docker-compose down
docker-compose up -d
```

### Step 7: Test It! ✅

1. **Schedule a Consultation**
   - Log in as a doctor
   - Select a patient
   - Click "Schedule Consultation"
   - Choose a future date/time
   - Submit

2. **Check the Response**
   - You should see a link like: `https://meet.google.com/abc-defg-hij-klm`
   - NOT a mock link like: `https://meet.google.com/mock-8830-ecf7`

3. **Verify the Link Works**
   - Copy the link and open it in your browser
   - You should see a real Google Meet interface
   - Calendar invites should be sent to doctor and patient emails

---

## 🔍 Troubleshooting

### Problem: Still getting mock links

**Solution:**
1. Verify all three credentials are in your `.env`:
   ```bash
   grep -E "GOOGLE_CLIENT_ID|GOOGLE_CLIENT_SECRET|GOOGLE_REFRESH_TOKEN" .env
   ```

2. Check `FEATURE_VIDEO_CALLS=true`:
   ```bash
   grep "FEATURE_VIDEO_CALLS" .env
   ```

3. Restart the backend (don't just reload, fully restart)

4. Check logs for:
   ```bash
   grep "Google Meet" logs/saramedico.log
   ```

### Problem: "Failed to generate Google Meet link" error

**Solutions:**

1. **Refresh token expired:**
   - Run Step 4 again to get a new refresh token

2. **Google Calendar API not enabled:**
   - Go to Google Cloud Console
   - APIs & Services → Library
   - Search for "Google Calendar API"
   - Make sure it's "Enabled"

3. **Incorrect credentials:**
   - Double-check copy-paste in `.env`
   - No extra spaces or quotes around values

4. **Account doesn't support Google Meet:**
   - Ensure your Google account is a Google Workspace account or personal account with Meet enabled
   - Try with a different Google account

### Problem: Authentication errors in logs

**Check:**
```bash
tail -100 logs/saramedico.log | grep -i "auth\|google"
```

Common causes:
- Credentials file path issue
- Expired refresh token
- Mismatched Client ID/Secret

---

## 📋 Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `GOOGLE_CLIENT_ID` | OAuth 2.0 Client ID | `123456789.apps.googleusercontent.com` |
| `GOOGLE_CLIENT_SECRET` | OAuth 2.0 Client Secret | `GOCSPX-xxxxx...` |
| `GOOGLE_REFRESH_TOKEN` | Refresh token for API access | `1//0gxxxxx...` |
| `FEATURE_VIDEO_CALLS` | Enable real Google Meet | `true` |

---

## 🎯 What Happens Now

### Before (Mock Links)
```
User schedules consultation
  ↓
System generates random mock link
  ↓
Link looks like: https://meet.google.com/mock-8830-ecf7
  ↓
❌ Link is INVALID - doesn't work
```

### After (Real Google Meet)
```
User schedules consultation
  ↓
System calls Google Calendar API with credentials
  ↓
Google creates real calendar event + Meet room
  ↓
Link looks like: https://meet.google.com/abc-defg-hij-klm
  ↓
✅ Link is VALID - opens real Google Meet
  ↓
Calendar invites sent to doctor & patient emails
```

---

## 📞 Support

If you encounter issues:

1. **Check logs:**
   ```bash
   tail -50 logs/saramedico.log | grep -i "google\|meet\|error"
   ```

2. **Verify credentials:**
   ```bash
   python3 -c "from app.services.google_meet_service import google_meet_service; print(google_meet_service._available)"
   ```

3. **Test Google API access:**
   ```python
   from google.oauth2.credentials import Credentials
   from googleapiclient.discovery import build
   
   creds = Credentials(
       token=None,
       refresh_token="YOUR_REFRESH_TOKEN",
       token_uri="https://oauth2.googleapis.com/token",
       client_id="YOUR_CLIENT_ID",
       client_secret="YOUR_CLIENT_SECRET"
   )
   service = build('calendar', 'v3', credentials=creds)
   calendars = service.calendarList().list().execute()
   print(calendars)
   ```

---

## ✨ Next Steps

Once real Google Meet is working:

1. **Enable other features** in `.env`:
   - `FEATURE_AI_ANALYSIS=true` for SOAP note generation
   - `FEATURE_REAL_EMAIL=true` for actual email sending

2. **Set up email notifications** for calendar invites:
   - Doctor and patient receive calendar invites automatically
   - Transcripts are captured after meeting ends

3. **Configure HIPAA compliance:**
   - Ensure Google Meet recordings are stored securely
   - Follow your organization's data retention policies

---

## 📚 Useful Links

- [Google Calendar API Docs](https://developers.google.com/calendar/api)
- [Google Meet Features](https://support.google.com/meet/answer/9308681)
- [OAuth 2.0 Setup](https://developers.google.com/identity/protocols/oauth2)

---

**Happy consulting! 🎉**
