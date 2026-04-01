# Deployment Checklist - Security Fixes

## Pre-Deployment

### Code Changes Verification
- [x] Issue #1: MinIO cleanup in `delete_my_account()` - DONE
- [x] Issue #2: Rate limiting decorators - DONE
- [x] Issue #3: Password strength validators - DONE
- [x] Issue #5: AI consent model and endpoints - DONE
- [x] Issue #6: Token TTL reduced to 15 min - DONE
- [x] Issue #7: Log level changed to WARNING - DONE
- [x] Issue #8: Email credentials replaced with tokens - DONE
- [x] Issue #9: About page created - DONE

### Environment Setup
- [ ] Copy new `.env` settings (see below)
- [ ] Verify no DEBUG logging in production config
- [ ] Verify JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
- [ ] Verify LOG_LEVEL=WARNING

### Dependencies
```bash
# Install rate limiting
pip install slowapi>=0.1.9

# Update requirements.txt
pip freeze > requirements.txt
```

### Database
- [ ] Run migration for AI consent field:
  ```bash
  alembic revision --autogenerate -m "Add AI consent field to users"
  alembic upgrade head
  ```
- [ ] Verify migration succeeds in staging

### Documentation
- [ ] Update Privacy Policy with AI provider disclosure
- [ ] Update Terms of Service if needed
- [ ] Brief customer support on changes

---

## Staging Deployment

### 1. Deploy Code Changes
```bash
# Pull latest code
git pull origin main

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head
```

### 2. Configure Environment
```bash
# Set in .env
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
LOG_LEVEL=WARNING
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30
```

### 3. Run Tests
```bash
# Test password validation
pytest tests/auth/test_password_strength.py

# Test rate limiting
pytest tests/auth/test_rate_limiting.py

# Test AI consent
pytest tests/ai/test_consent.py

# Test document cleanup
pytest tests/auth/test_delete_account.py

# Full test suite
pytest
```

### 4. Verification Tests
```bash
# 1. Test token expiry (should fail after 15 min)
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"SecureP@ss123"}' \
  | jq -r '.access_token')

# Wait 15 minutes
sleep 900

# Should return 401
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"

# 2. Test rate limiting
for i in {1..6}; do
  curl -X POST http://localhost:8000/api/v1/auth/register \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"user$i@test.com\",\"password\":\"Test@123\"}" &
done
wait
# 6th request should return 429

# 3. Test password strength
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"weak@test.com","password":"weak"}'
# Should return 422

# 4. Test AI consent requirement
curl -X POST http://localhost:8000/api/v1/doctor/ai/process-document \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"patient_id":"test","document_id":"test"}'
# Should return 403 if consent not granted

# 5. Check logging
tail -f logs/saramedico.log
# Should only show WARNING, ERROR (no DEBUG)
```

### 5. Load Testing
```bash
# Test rate limiting under load
ab -n 1000 -c 10 -H "Content-Type: application/json" \
  -p login.json http://localhost:8000/api/v1/auth/login
# Should return proper rate limit responses
```

---

## Production Deployment

### Pre-Flight Checks
- [ ] All staging tests passed
- [ ] Database backup created
- [ ] Rollback plan ready
- [ ] Customer communication sent
- [ ] Support team briefed on changes

### Deployment Steps
```bash
# 1. Backup database
pg_dump saramedico_db > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Pull latest code
git pull origin main

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run migrations
alembic upgrade head

# 5. Update environment variables
# Set JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
# Set LOG_LEVEL=WARNING

# 6. Restart application
systemctl restart saramedico-backend
# or
docker-compose restart backend
```

### Post-Deployment Monitoring
- [ ] Check application is running: `curl http://localhost:8000/health`
- [ ] Monitor error logs: `tail -f logs/saramedico.log`
- [ ] Verify no DEBUG messages in logs
- [ ] Monitor API response times (should be similar)
- [ ] Monitor failed login attempts (should increase due to rate limiting)
- [ ] Monitor token expiry errors (expected with 15-min TTL)

### Rollback Procedure (if needed)
```bash
# 1. Restore database
psql saramedico_db < backup_20260401_120000.sql

# 2. Revert code
git revert <commit-hash>

# 3. Restart application
systemctl restart saramedico-backend

# 4. Notify customers
# Email: Users may need to login again
```

---

## Post-Deployment Tasks

### 1. Customer Communication
Send email to customers:
```
Subject: Security Enhancements - SaraMedico Update

We've deployed important security enhancements:

• Access tokens now expire every 15 minutes (was 24 hours) - use refresh tokens for long sessions
• Stronger password requirements (8+ chars with uppercase, number, special char)
• Rate limiting on login and registration to prevent attacks
• Secure setup links instead of passwords for new accounts
• AI processing now requires explicit patient consent
• Debug logging disabled in production

No action needed from you. Your existing sessions remain valid.
Questions? Contact support@saramedico.com
```

### 2. Monitoring Dashboard Setup
Monitor these metrics:
- Failed login attempts (should spike due to rate limiting)
- Token expiration errors (expected with 15-min TTL)
- Log message distribution (should be WARNING/ERROR only)
- Password strength validation failures
- AI consent grant/revoke events
- Account deletion requests

### 3. Security Audit
- [ ] Review all logs for anomalies
- [ ] Check for any bypass attempts
- [ ] Verify MinIO cleanup on deleted accounts
- [ ] Test delete account flow end-to-end
- [ ] Verify Apple Sign-In before iOS release

---

## Frontend Tasks (Separate)

These need frontend team attention:

### 1. About Page Integration
```bash
# Add route in Next.js app router
import AboutPage from '@/app/pages/about';

// In app.tsx or routing config
<Route path="/about" element={<AboutPage />} />
```

### 2. Delete Account UI
Add to patient/doctor settings:
```jsx
// In Settings component
<Box sx={{ backgroundColor: '#FEE2E2', p: 3, borderRadius: 2, mt: 4 }}>
  <Typography variant="h6" sx={{ color: '#991B1B', mb: 2 }}>
    Danger Zone
  </Typography>
  <Button 
    variant="contained" 
    color="error"
    onClick={handleDeleteAccount}
  >
    Delete Account Permanently
  </Button>
</Box>
```

### 3. API Endpoint for Setup Link
Create `/auth/setup?token=...` page to:
- Accept setup token from email link
- Allow user to set their own password
- Redirect to login after password setup

---

## Issue-Specific Verification

### Issue #1: MinIO Cleanup
```bash
# Verify in database deletion process
docker logs saramedico-backend | grep "MinIO delete"
# Should show: "[DeleteAccount] MinIO delete for document"
```

### Issue #2: Rate Limiting
```bash
# Should be present in logs
grep "@limiter.limit" app/api/v1/auth.py
# Output: 3 matches
```

### Issue #3: Password Strength
```bash
# Test various passwords
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test@123"}'
# Should succeed

curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"nospecialchar123"}'
# Should fail with validation error
```

### Issue #5: AI Consent
```bash
# Verify field exists in database
psql saramedico_db -c "SELECT column_name FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'ai_processing_consented';"
# Should return 1 row

# Test consent flow
curl -X POST http://localhost:8000/api/v1/doctor/ai/consent \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"consented":true}'
```

### Issue #6: Token TTL
```bash
# Verify config
grep "JWT_ACCESS_TOKEN_EXPIRE_MINUTES" app/config.py
# Should show: 15

# Test token expiry
# Login, wait 15 minutes, token should be rejected
```

### Issue #7: Log Level
```bash
# Verify config
grep "LOG_LEVEL" app/config.py
# Should show: WARNING

# Verify in logs (should have no DEBUG messages)
tail -100 logs/saramedico.log | grep DEBUG
# Should return nothing
```

### Issue #8: Email Credentials
```bash
# Verify function signature
grep -A 5 "send_doctor_credentials_email" app/services/email.py
# Should show: setup_token parameter (not password)
```

---

## Rollback Testing (Staging Only)

Test rollback procedure in staging:
```bash
# 1. Deploy new code
git checkout main && git pull

# 2. Run full test suite
pytest

# 3. Rollback
git revert HEAD

# 4. Verify rollback works
pytest

# 5. Deploy again
git checkout main
```

---

## Sign-Off Checklist

Before marking deployment complete:

**QA/Testing:**
- [ ] All automated tests pass
- [ ] Manual testing completed
- [ ] Load testing passed
- [ ] Rollback tested successfully

**Operations:**
- [ ] Deployment documented
- [ ] Monitoring alerts configured
- [ ] Support team trained
- [ ] Customer communication sent

**Security:**
- [ ] No DEBUG logging in production
- [ ] Rate limiting verified
- [ ] Token expiry confirmed
- [ ] AI consent working
- [ ] Password strength enforced

**Business:**
- [ ] Zero issues reported by customers
- [ ] Performance metrics normal
- [ ] No security alerts triggered

---

## Contact & Escalation

**Issue During Deployment?**
1. Contact: [DevOps Lead]
2. Escalate: [Engineering Manager]
3. Emergency: [CTO]

**Performance Issues?**
- Check rate limiting not too aggressive
- Verify token expiry not causing session issues
- Monitor CPU/memory (logging changes shouldn't impact)

**Security Issues?**
- Contact security team immediately
- Prepare incident response
- Document all changes

---

**Deployment Version:** 1.0.0  
**Date Prepared:** April 1, 2026  
**Last Updated:** [Auto-updated on deployment]
