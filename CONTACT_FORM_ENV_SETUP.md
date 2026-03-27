# Contact Form API - Environment Configuration

## Add these variables to your `.env` file

### Contact Form Email Configuration
```bash
# The email address where contact form submissions will be sent
# This will be used in the send_contact_form_email() function
ENTERPRISE_EMAIL=enterprise@saramedico.com

# Alternative examples:
# ENTERPRISE_EMAIL=contact@yourcompany.com
# ENTERPRISE_EMAIL=support@yourcompany.com
# ENTERPRISE_EMAIL=info@yourcompany.com
# ENTERPRISE_EMAIL=sales@yourcompany.com
```

### SMTP Configuration (Required for Email Sending)

#### Gmail Setup
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME=Saramedico
SMTP_TLS=true
SMTP_SSL=false
```

**Note:** Use App Passwords, not your regular Gmail password!  
Get it here: https://myaccount.google.com/apppasswords

#### Microsoft 365 / Outlook Setup
```bash
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USER=your-email@outlook.com
SMTP_PASSWORD=your-password
SMTP_FROM_EMAIL=your-email@outlook.com
SMTP_FROM_NAME=Saramedico
SMTP_TLS=true
SMTP_SSL=false
```

#### SendGrid Setup
```bash
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=SG.your-sendgrid-api-key
SMTP_FROM_EMAIL=noreply@yourcompany.com
SMTP_FROM_NAME=Saramedico
SMTP_TLS=true
SMTP_SSL=false
```

#### AWS SES Setup
```bash
SMTP_HOST=email-smtp.region.amazonaws.com
SMTP_PORT=587
SMTP_USER=your-smtp-username
SMTP_PASSWORD=your-smtp-password
SMTP_FROM_EMAIL=noreply@yourcompany.com
SMTP_FROM_NAME=Saramedico
SMTP_TLS=true
SMTP_SSL=false
```

#### Generic SMTP Server
```bash
SMTP_HOST=mail.yourserver.com
SMTP_PORT=587
SMTP_USER=your-username
SMTP_PASSWORD=your-password
SMTP_FROM_EMAIL=noreply@yourcompany.com
SMTP_FROM_NAME=Saramedico
SMTP_TLS=true
SMTP_SSL=false
```

---

## Complete Example .env

Here's a complete example with all variables:

```bash
# ===== APPLICATION =====
APP_NAME=Saramedico
APP_ENV=development
APP_DEBUG=true
APP_VERSION=1.0.0
APP_SECRET_KEY=your-secret-key-here

# ===== API =====
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
API_V1_PREFIX=/api/v1

# ===== CORS =====
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
FRONTEND_URL=http://localhost:3000

# ===== SECURITY =====
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30
REFRESH_TOKEN_EXPIRE_DAYS=30
ENCRYPTION_KEY=your-encryption-key

# ===== DATABASE =====
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/saramedico
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
DATABASE_POOL_TIMEOUT=30

# ===== REDIS =====
REDIS_URL=redis://localhost:6379
REDIS_DB_CACHE=0
REDIS_DB_SESSIONS=1
REDIS_DB_CELERY=2

# ===== MINIO =====
MINIO_ENDPOINT=localhost:9000
MINIO_EXTERNAL_ENDPOINT=http://localhost:9000
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
MINIO_USE_SSL=false
MINIO_BUCKET_UPLOADS=saramedico-uploads
MINIO_BUCKET_DOCUMENTS=saramedico-medical-records
MINIO_BUCKET_AUDIO=saramedico-audio-logs
MINIO_BUCKET_AVATARS=saramedico-avatars
PRESIGNED_URL_EXPIRY=3600

# ===== EMAIL (CONTACT FORM) =====
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME=Saramedico
SMTP_TLS=true
SMTP_SSL=false

# Contact form email destination
ENTERPRISE_EMAIL=enterprise@saramedico.com

# ===== CELERY =====
CELERY_BROKER_URL=redis://localhost:6379/2
CELERY_RESULT_BACKEND=redis://localhost:6379/2
CELERY_TASK_SERIALIZER=json
CELERY_ACCEPT_CONTENT=json
CELERY_TIMEZONE=UTC

# ===== MFA =====
MFA_ENABLED=true
MFA_ISSUER_NAME=Saramedico
TOTP_SECRET_LENGTH=32
OTP_EXPIRY_SECONDS=300
OTP_RESEND_COOLDOWN_SECONDS=60
OTP_MAX_ATTEMPTS=5

# ===== RATE LIMITING =====
RATE_LIMIT_PER_MINUTE=60
LOGIN_RATE_LIMIT_PER_MINUTE=5

# ===== FILE UPLOADS =====
MAX_UPLOAD_SIZE_MB=100
ALLOWED_FILE_EXTENSIONS=pdf,jpg,jpeg,png,gif,wav,mp3,m4a,webm,dicom,docx,txt

# ===== AUDIT LOGGING =====
AUDIT_LOG_ENABLED=true
AUDIT_LOG_RETENTION_DAYS=2555

# ===== SESSION MANAGEMENT =====
SESSION_EXPIRY_HOURS=24
MAX_CONCURRENT_SESSIONS=5
SESSION_IDLE_TIMEOUT_MINUTES=30

# ===== SUBSCRIPTION (Trial Mode) =====
TRIAL_DURATION_DAYS=10
TRIAL_PATIENTS_LIMIT=10
TRIAL_STORAGE_LIMIT_MB=500

# ===== LOGGING =====
LOG_LEVEL=DEBUG
LOG_FORMAT=json
LOG_FILE_PATH=logs/saramedico.log

# ===== FEATURE FLAGS =====
FEATURE_AI_ANALYSIS=false
FEATURE_VIDEO_CALLS=false
FEATURE_SMS_NOTIFICATIONS=false
FEATURE_REAL_EMAIL=false
FEATURE_CLOUD_STORAGE=false

# ===== ZOOM =====
ZOOM_ACCOUNT_ID=
ZOOM_CLIENT_ID=
ZOOM_CLIENT_SECRET=
ZOOM_ADMIN_EMAIL=
ZOOM_BASE_URL=https://api.zoom.us/v2
ZOOM_AUTH_URL=https://zoom.us/oauth/token

# ===== GOOGLE OAUTH =====
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback
GOOGLE_REFRESH_TOKEN=

# ===== APPLE AUTH =====
APPLE_CLIENT_ID=
APPLE_CLIENT_SECRET=
APPLE_REDIRECT_URI=
```

---

## Testing Configuration

After setting up your `.env`, test the configuration:

### 1. Test Email Service

```bash
python -c "
import asyncio
from app.services.email import send_contact_form_email

async def test():
    result = await send_contact_form_email(
        sender_name='Test User',
        sender_email='test@example.com',
        sender_phone='+1-555-123-4567',
        subject='Test Message',
        message='This is a test message from the contact form.'
    )
    print(f'Email sent: {result}')

asyncio.run(test())
"
```

### 2. Test API Endpoint

```bash
curl -X POST http://localhost:8000/api/v1/contact/submit \
  -H "Content-Type: application/json" \
  -d '{
    "firstName": "John",
    "lastName": "Doe",
    "email": "john@example.com",
    "phone": "+1-555-123-4567",
    "subject": "Test",
    "message": "This is a test message"
  }'
```

---

## Email Provider Recommendations

| Provider | Best For | Cost | Setup Complexity |
|----------|----------|------|------------------|
| **Gmail** | Testing/Small | Free | Easy |
| **SendGrid** | Production | $10-100/mo | Medium |
| **AWS SES** | High volume | Cheap | Medium |
| **Microsoft 365** | Enterprise | $5-20/user/mo | Medium |
| **Mailgun** | Production | $10-50/mo | Medium |

---

## Security Best Practices

1. **Never commit `.env` to git**
   ```bash
   # Add to .gitignore
   echo ".env" >> .gitignore
   ```

2. **Use strong passwords/keys**
   ```bash
   # Generate secure random strings
   openssl rand -base64 32
   ```

3. **Rotate credentials regularly**
   - Change SMTP passwords every 90 days
   - Rotate API keys quarterly

4. **Use environment-specific credentials**
   - Different email for dev and production
   - Separate API keys per environment

5. **Mask sensitive data in logs**
   ```bash
   # Don't log passwords or API keys
   LOG_LEVEL=INFO  # Use INFO instead of DEBUG in production
   ```

---

## Troubleshooting Email Issues

### Error: "Connection refused"
- Check SMTP_HOST and SMTP_PORT are correct
- Verify SMTP server is accessible from your server
- Check firewall rules

### Error: "Authentication failed"
- Verify SMTP_USER and SMTP_PASSWORD
- For Gmail: Use App Password, not regular password
- Check if account requires 2FA setup

### Error: "SSL certificate problem"
- Set SMTP_TLS=true or SMTP_SSL=false
- Update SSL certificates on server

### Email not received
- Check ENTERPRISE_EMAIL is correct
- Verify email is not in spam folder
- Check email provider logs

---

## Helpful Commands

```bash
# Test SMTP connection
telnet smtp.gmail.com 587

# Verify DNS MX records
nslookup -type=MX yourdomain.com

# Check SSL certificate
openssl s_client -connect smtp.gmail.com:587

# View environment variables
env | grep SMTP

# Reload environment variables (Docker)
docker-compose down && docker-compose up -d
```

---

## Summary

**Minimum Required Variables for Contact Form:**
- `ENTERPRISE_EMAIL` - Where to send submissions
- `SMTP_HOST` - Email server hostname
- `SMTP_PORT` - Email server port
- `SMTP_USER` - SMTP username
- `SMTP_PASSWORD` - SMTP password
- `SMTP_FROM_EMAIL` - Sender email address
- `SMTP_FROM_NAME` - Sender name

All other variables have defaults and are optional!
