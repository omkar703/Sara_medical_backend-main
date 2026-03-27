# ✅ Real Google Meet Quick Start Checklist

## What Was Fixed
- ❌ **Old:** Mock links like `https://meet.google.com/mock-8830-ecf7` (invalid)
- ✅ **New:** Real links like `https://meet.google.com/abc-defg-hij-klm` (valid)

---

## 5-Minute Setup

### ☐ Step 1: Get Google Credentials (5 mins)

1. **Go to:** https://console.cloud.google.com/
2. **Create new project** → Name: "Saramedico"
3. **Enable Google Calendar API**
   - APIs & Services → Library
   - Search "Google Calendar API" → Enable
4. **Create OAuth 2.0 credentials**
   - APIs & Services → Credentials → Create Credentials
   - Choose "Desktop application"
   - Copy `client_id` and `client_secret`
5. **Get Refresh Token**
   ```bash
   # Install required packages if needed:
   pip install google-auth-oauthlib
   
   # Run this to get your refresh token:
   python3 -c "
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.client_config import ClientConfig

config = {
    'installed': {
        'type': 'desktop',
        'client_id': 'YOUR_CLIENT_ID',
        'client_secret': 'YOUR_CLIENT_SECRET',
        'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
        'token_uri': 'https://oauth2.googleapis.com/token',
        'auth_provider_x509_cert_url': 'https://www.googleapis.com/oauth2/v1/certs',
        'redirect_uris': ['http://localhost']
    }
}

scopes = [
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/drive.readonly'
]

flow = InstalledAppFlow.from_client_config(config, scopes)
creds = flow.run_local_server(port=8080)
print('GOOGLE_REFRESH_TOKEN=' + creds.refresh_token)
   "
   ```

### ☐ Step 2: Update .env File (1 min)

Add to your `.env` file:

```env
GOOGLE_CLIENT_ID=YOUR_CLIENT_ID
GOOGLE_CLIENT_SECRET=YOUR_CLIENT_SECRET
GOOGLE_REFRESH_TOKEN=YOUR_REFRESH_TOKEN
FEATURE_VIDEO_CALLS=true
```

### ☐ Step 3: Restart Backend (1 min)

```bash
# Local development:
# (Stop with Ctrl+C, then restart)
python -m uvicorn app.main:app --reload

# Docker:
docker-compose down
docker-compose up -d
```

### ☐ Step 4: Verify (1 min)

```bash
# Run verification script
python3 verify_google_meet.py
```

You should see:
```
✅ SUCCESS! Google Meet is properly configured!

Meet Link: https://meet.google.com/abc-defg-hij-klm
```

---

## 🧪 Test in App

1. Log in as a doctor
2. Schedule a consultation
3. **Check the response:**
   - ✅ Should see: `https://meet.google.com/abc-defg-hij-klm`
   - ❌ NOT: `https://meet.google.com/mock-8830-ecf7`
4. **Click the link** → Should open real Google Meet

---

## 🔧 If Still Getting Mock Links

1. **Check credentials are in .env:**
   ```bash
   cat .env | grep GOOGLE
   ```

2. **Check no typos:**
   - No extra spaces
   - Correct format: `GOOGLE_CLIENT_ID=value` (no quotes)

3. **Fully restart backend:**
   - Kill the process (Ctrl+C)
   - Restart the command
   - (Just "reload" won't load new .env vars)

4. **Check logs:**
   ```bash
   tail -50 logs/saramedico.log | grep -i google
   ```

---

## 🆘 Common Issues

| Issue | Solution |
|-------|----------|
| Still getting mock links | Make sure backend is fully restarted after .env changes |
| "Failed to generate Google Meet link" | Refresh token expired - regenerate it |
| "Google API not initialized" | Verify all 3 credentials are in .env |
| Error about calendar API | Go to Cloud Console → APIs & Services → Check Calendar API is Enabled |

---

## 📞 Need Help?

1. **Full setup guide:** See `GOOGLE_MEET_SETUP.md`
2. **Detailed API docs:** See `.env.google-meet.example`
3. **Verify setup:** Run `python3 verify_google_meet.py`
4. **Check logs:** `tail -100 logs/saramedico.log | grep -i google`

---

## ✨ What's Next?

After Google Meet is working:

- ✅ Consultations generate real meeting links
- ✅ Doctor & patient get calendar invites
- ✅ Meetings can be recorded
- ✅ Transcripts available for AI SOAP notes

Enable more features:
```env
FEATURE_AI_ANALYSIS=true        # Auto-generate SOAP notes
FEATURE_REAL_EMAIL=true         # Send real emails
FEATURE_SMS_NOTIFICATIONS=true  # Send SMS alerts
```

---

**Happy consulting! 🎉**
