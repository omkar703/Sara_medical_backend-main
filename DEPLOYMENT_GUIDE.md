# 🚀 Saramedico Backend Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the Saramedico Backend on any system with Docker and Docker Compose installed.

---

## 📋 Prerequisites

### Required Software

- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher
- **Git**: For cloning the repository

### System Requirements

- **OS**: Linux, macOS, or Windows with WSL2
- **RAM**: Minimum 4GB (8GB recommended)
- **Disk Space**: Minimum 10GB free space
- **CPU**: 2 cores minimum (4 cores recommended)

### Verify Prerequisites

```bash
# Check Docker version
docker --version

# Check Docker Compose version
docker-compose --version

# Verify Docker is running
docker ps
```

---

## 🔧 Environment Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Sara_medical_backend-main
```

### 2. Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and configure the following critical variables:

```env
# Application
APP_NAME=Saramedico
APP_ENV=production
APP_DEBUG=false

# Database
DATABASE_NAME=saramedico_dev
DATABASE_USER=saramedico_user
DATABASE_PASSWORD=<CHANGE_THIS_SECURE_PASSWORD>
DATABASE_HOST=postgres
DATABASE_PORT=5432

# Redis
REDIS_PASSWORD=<CHANGE_THIS_SECURE_PASSWORD>

# MinIO
MINIO_ROOT_USER=saramedico_minio_admin
MINIO_ROOT_PASSWORD=<CHANGE_THIS_SECURE_PASSWORD>

# JWT Secret (IMPORTANT: Generate a secure random string)
JWT_SECRET_KEY=<GENERATE_SECURE_RANDOM_STRING>

# Encryption Key (IMPORTANT: Generate a secure random string)
ENCRYPTION_KEY=<GENERATE_SECURE_RANDOM_STRING>
```

### 3. Generate Secure Keys

```bash
# Generate JWT secret (32+ characters)
openssl rand -hex 32

# Generate encryption key (32+ characters)
openssl rand -hex 32
```

**⚠️ IMPORTANT**: Store these keys securely and never commit them to version control!

---

## 🐳 Docker Deployment

### First-Time Deployment

#### Step 1: Build Docker Images

```bash
# Build all images
docker-compose build

# Or build with no cache (clean build)
docker-compose build --no-cache
```

#### Step 2: Start Services

```bash
# Start all services in detached mode
docker-compose up -d
```

#### Step 3: Verify Services

```bash
# Check service status
docker-compose ps

# All services should show "Up" and "healthy"
```

#### Step 4: Run Database Migrations

```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Verify current migration
docker-compose exec backend alembic current
```

#### Step 5: Health Check

```bash
# Run comprehensive health check
./scripts/health-check.sh

# Or check via API
curl http://localhost:8000/health
```

---

## 🔍 Verification

### 1. Check Service Health

```bash
# Check all services
docker-compose ps

# Expected output: All services should be "Up" and "healthy"
```

### 2. Access Web Interfaces

- **API Documentation**: http://localhost:8000/docs
- **API Alternative Docs**: http://localhost:8000/redoc
- **MinIO Console**: http://localhost:9011
- **MailHog UI**: http://localhost:8030

### 3. Test API Endpoints

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test database health
curl http://localhost:8000/health/database

# Test Redis health
curl http://localhost:8000/health/redis

# Test MinIO health
curl http://localhost:8000/health/minio
```

### 4. View Logs

```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs backend

# Follow logs in real-time
docker-compose logs -f backend

# View last 100 lines
docker-compose logs --tail=100 backend
```

---

## 🧪 Running Tests

### Inside Docker Container

```bash
# Run all tests
docker-compose exec backend pytest tests/ -v

# Run specific test file
docker-compose exec backend pytest tests/test_complete_endpoints.py -v

# Run E2E tests
docker-compose exec backend pytest tests/test_e2e_complete_flow.py -v

# Run with coverage
docker-compose exec backend pytest tests/ --cov=app --cov-report=term-missing
```

### Using Test Script

```bash
# Run comprehensive test suite
docker-compose exec backend ./scripts/run-tests.sh
```

---

## 🔄 Common Operations

### Restart Services

```bash
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart backend
```

### Stop Services

```bash
# Stop all services
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop and remove containers + volumes (⚠️ deletes data)
docker-compose down -v
```

### Update Application

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose build
docker-compose up -d

# Run migrations if needed
docker-compose exec backend alembic upgrade head
```

### View Database

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U saramedico_user -d saramedico_dev

# List tables
\dt

# Exit
\q
```

### Access Backend Shell

```bash
# Access backend container shell
docker-compose exec backend /bin/bash

# Access Python shell
docker-compose exec backend python

# Access Alembic
docker-compose exec backend alembic --help
```

---

## 📊 Monitoring

### Resource Usage

```bash
# View resource usage
docker stats

# View specific container
docker stats saramedico_backend
```

### Disk Usage

```bash
# Check Docker disk usage
docker system df

# Clean up unused resources
docker system prune
```

---

## 🛠️ Troubleshooting

### Services Not Starting

```bash
# Check logs for errors
docker-compose logs

# Check specific service
docker-compose logs backend

# Rebuild from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### Database Connection Issues

```bash
# Check database is running
docker-compose ps postgres

# Check database logs
docker-compose logs postgres

# Verify database credentials in .env
cat .env | grep DATABASE
```

### Permission Errors

```bash
# Fix file permissions
sudo chown -R $USER:$USER .

# Recreate containers
docker-compose down
docker-compose up -d
```

### Port Conflicts

If ports are already in use, edit `docker-compose.yml` to change port mappings:

```yaml
ports:
  - "8001:8000" # Change 8000 to 8001
```

---

## 🔒 Security Checklist

Before deploying to production:

- [ ] Change all default passwords in `.env`
- [ ] Generate secure JWT secret key
- [ ] Generate secure encryption key
- [ ] Set `APP_DEBUG=false`
- [ ] Set `APP_ENV=production`
- [ ] Configure CORS origins properly
- [ ] Enable HTTPS/SSL
- [ ] Set up firewall rules
- [ ] Configure backup strategy
- [ ] Review and update security headers
- [ ] Enable rate limiting
- [ ] Set up monitoring and alerting

---

## 📦 Backup and Restore

### Backup Database

```bash
# Create backup
docker-compose exec postgres pg_dump -U saramedico_user saramedico_dev > backup_$(date +%Y%m%d_%H%M%S).sql

# Or use pg_dumpall for all databases
docker-compose exec postgres pg_dumpall -U saramedico_user > backup_all_$(date +%Y%m%d_%H%M%S).sql
```

### Restore Database

```bash
# Restore from backup
cat backup_20260128_120000.sql | docker-compose exec -T postgres psql -U saramedico_user -d saramedico_dev
```

### Backup MinIO Data

```bash
# Backup MinIO volumes
docker run --rm -v saramedico_minio_data:/data -v $(pwd):/backup alpine tar czf /backup/minio_backup_$(date +%Y%m%d_%H%M%S).tar.gz /data
```

---

## 🌐 Production Deployment

### Additional Considerations

1. **Reverse Proxy**: Use Nginx or Traefik
2. **SSL/TLS**: Configure Let's Encrypt certificates
3. **Load Balancing**: Scale backend workers
4. **Monitoring**: Set up Prometheus + Grafana
5. **Logging**: Configure centralized logging (ELK stack)
6. **Secrets Management**: Use Docker secrets or vault
7. **CI/CD**: Set up automated deployments

### Example Nginx Configuration

```nginx
server {
    listen 80;
    server_name api.saramedico.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 📞 Support

For issues or questions:

1. Check logs: `docker-compose logs`
2. Review this guide
3. Check API documentation: http://localhost:8000/docs
4. Contact support team

---

## ✅ Deployment Checklist

- [ ] Prerequisites installed (Docker, Docker Compose)
- [ ] Repository cloned
- [ ] `.env` file configured with secure credentials
- [ ] Docker images built successfully
- [ ] All services started and healthy
- [ ] Database migrations completed
- [ ] Health checks passing
- [ ] API accessible at http://localhost:8000
- [ ] Tests passing
- [ ] Backup strategy configured
- [ ] Security checklist completed (for production)

---

**🎉 Congratulations! Your Saramedico Backend is now deployed and ready to use!**
