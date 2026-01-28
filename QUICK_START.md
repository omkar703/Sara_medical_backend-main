# 🚀 Quick Start Guide - Saramedico Backend

## For Deployment Team

This guide helps you quickly deploy and verify the Saramedico Backend on any system.

---

## ⚡ Quick Deployment (5 Minutes)

### Step 1: Prerequisites Check (30 seconds)

```bash
# Verify Docker is installed
docker --version
# Expected: Docker version 20.10+

# Verify Docker Compose is installed
docker compose version
# Expected: Docker Compose version 2.0+
```

### Step 2: Clone and Configure (1 minute)

```bash
# Clone repository
git clone <repository-url>
cd Sara_medical_backend-main

# Copy environment file
cp .env.example .env

# IMPORTANT: Edit .env and set secure passwords
# At minimum, change these:
# - DATABASE_PASSWORD
# - REDIS_PASSWORD
# - MINIO_ROOT_PASSWORD
# - JWT_SECRET_KEY
# - ENCRYPTION_KEY
```

### Step 3: Build and Start (3 minutes)

```bash
# Build all services
docker compose build

# Start all services
docker compose up -d

# Wait for services to be healthy (30-60 seconds)
sleep 60
```

### Step 4: Verify Deployment (30 seconds)

```bash
# Check all services are running
docker compose ps
# All should show "Up" and "healthy"

# Test API
curl http://localhost:8000/health
# Should return: {"status": "healthy", ...}

# Access API docs
# Open browser: http://localhost:8000/docs
```

---

## ✅ Verification Checklist

Run these commands to verify everything works:

```bash
# 1. Check services
docker compose ps
# ✅ All services should be "Up (healthy)"

# 2. Check database
curl http://localhost:8000/health/database
# ✅ Should return healthy status

# 3. Check Redis
curl http://localhost:8000/health/redis
# ✅ Should return healthy status

# 4. Check MinIO
curl http://localhost:8000/health/minio
# ✅ Should return healthy status

# 5. Run migrations
docker compose exec backend alembic upgrade head
# ✅ Should complete without errors

# 6. Run tests
docker compose exec backend pytest tests/test_health.py -v
# ✅ All tests should pass
```

---

## 🧪 Running Tests

### Quick Test (1 minute)

```bash
# Test health endpoints
docker compose exec backend pytest tests/test_health.py -v
```

### Full Test Suite (5-10 minutes)

```bash
# Run all tests
docker compose exec backend pytest tests/ -v

# Or use the test script
docker compose exec backend ./scripts/run-tests.sh
```

### Test Specific Features

```bash
# Test authentication
docker compose exec backend pytest tests/test_complete_endpoints.py::TestAuthenticationEndpoints -v

# Test appointments
docker compose exec backend pytest tests/test_complete_endpoints.py::TestAppointmentEndpoints -v

# Test permissions
docker compose exec backend pytest tests/test_complete_endpoints.py::TestPermissionEndpoints -v

# Test E2E flows
docker compose exec backend pytest tests/test_e2e_complete_flow.py -v
```

---

## 🔍 Access Points

After deployment, access these URLs:

| Service              | URL                          | Purpose                       |
| -------------------- | ---------------------------- | ----------------------------- |
| **API Swagger Docs** | http://localhost:8000/docs   | Interactive API documentation |
| **API ReDoc**        | http://localhost:8000/redoc  | Alternative API documentation |
| **Health Check**     | http://localhost:8000/health | Service health status         |
| **MinIO Console**    | http://localhost:9011        | Object storage management     |
| **MailHog UI**       | http://localhost:8030        | Email testing interface       |

### Default Credentials

**MinIO Console**:

- Username: `saramedico_minio_admin` (or from .env)
- Password: Check `MINIO_ROOT_PASSWORD` in .env

**Database** (if needed):

- Host: `localhost:5435`
- Database: `saramedico_dev`
- Username: `saramedico_user`
- Password: Check `DATABASE_PASSWORD` in .env

---

## 🛠️ Common Commands

### View Logs

```bash
# All services
docker compose logs

# Specific service
docker compose logs backend
docker compose logs postgres
docker compose logs redis

# Follow logs (real-time)
docker compose logs -f backend

# Last 100 lines
docker compose logs --tail=100 backend
```

### Restart Services

```bash
# Restart all
docker compose restart

# Restart specific service
docker compose restart backend
```

### Stop Services

```bash
# Stop all
docker compose stop

# Stop and remove containers
docker compose down

# Stop and remove everything (including volumes - ⚠️ deletes data)
docker compose down -v
```

### Database Operations

```bash
# Run migrations
docker compose exec backend alembic upgrade head

# Check current migration
docker compose exec backend alembic current

# Access database
docker compose exec postgres psql -U saramedico_user -d saramedico_dev
```

---

## 🚨 Troubleshooting

### Services Won't Start

```bash
# Check logs for errors
docker compose logs

# Rebuild from scratch
docker compose down -v
docker compose build --no-cache
docker compose up -d
```

### Port Already in Use

Edit `docker-compose.yml` and change port mappings:

```yaml
ports:
  - "8001:8000" # Change 8000 to 8001
```

### Database Connection Error

```bash
# Check database is running
docker compose ps postgres

# Check database logs
docker compose logs postgres

# Verify credentials in .env match docker-compose.yml
```

### Tests Failing

```bash
# Ensure all services are healthy
docker compose ps

# Run migrations
docker compose exec backend alembic upgrade head

# Check test database exists
docker compose exec postgres psql -U saramedico_user -l
```

---

## 📊 Health Check Script

Run comprehensive health check:

```bash
# Make script executable (if not already)
chmod +x scripts/health-check.sh

# Run health check
./scripts/health-check.sh

# Or from inside container
docker compose exec backend ./scripts/health-check.sh
```

Expected output:

```
🏥 Running comprehensive health checks...
Checking PostgreSQL... ✅ Healthy
Checking Redis... ✅ Healthy
Checking MinIO... ✅ Healthy
Checking Backend API... ✅ Healthy
=========================================
✅ All critical services are healthy!
```

---

## 🔒 Security Notes

Before production deployment:

1. **Change all default passwords** in `.env`
2. **Generate secure keys**:

   ```bash
   # JWT Secret
   openssl rand -hex 32

   # Encryption Key
   openssl rand -hex 32
   ```

3. **Set environment to production**:
   ```env
   APP_ENV=production
   APP_DEBUG=false
   ```
4. **Configure CORS** properly in `.env`
5. **Enable HTTPS** (use reverse proxy like Nginx)

---

## 📚 Additional Documentation

- **Full Deployment Guide**: `DEPLOYMENT_GUIDE.md`
- **Testing Guide**: `TESTING_GUIDE.md`
- **API Testing Results**: `API_TESTING_RESULTS.md`
- **API Documentation**: http://localhost:8000/docs (after deployment)

---

## ✅ Success Criteria

Your deployment is successful when:

- [ ] All services show "Up (healthy)" in `docker compose ps`
- [ ] Health check returns healthy status
- [ ] API docs accessible at http://localhost:8000/docs
- [ ] Database migrations completed
- [ ] Basic tests pass
- [ ] Can create a test user via API

---

## 📞 Need Help?

1. Check logs: `docker compose logs`
2. Review `DEPLOYMENT_GUIDE.md`
3. Check `TESTING_GUIDE.md` for test issues
4. Verify all prerequisites are met
5. Ensure .env is properly configured

---

**Estimated Total Time**: 5-10 minutes for first deployment  
**Estimated Test Time**: 5-10 minutes for full test suite

**🎉 You're ready to deploy!**
