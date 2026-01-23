# Saramedico Backend

HIPAA-Compliant Medical AI SaaS Platform Backend

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Git

### Setup

1. **Clone the repository** (if not already done)

   ```bash
   cd backend
   ```

2. **Environment configuration**
   - The `.env` file is already configured with strong passwords
   - Review `.env.example` for all available settings

3. **Start all services**

   ```bash
   docker-compose up -d
   ```

4. **Verify all services are running**

   ```bash
   docker-compose ps
   ```

   You should see:
   - ✅ saramedico_postgres (healthy)
   - ✅ saramedico_redis (healthy)
   - ✅ saramedico_minio (healthy)
   - ✅ saramedico_mailhog (healthy)
   - ✅ saramedico_backend (healthy)
   - ✅ saramedico_celery_worker (running)
   - ✅ saramedico_celery_beat (running)

5. **Check health endpoints**
   ```bash
   curl http://localhost:8000/health
   ```

### Access Points

- **API Documentation (Swagger):** http://localhost:8000/docs
- **API Documentation (ReDoc):** http://localhost:8000/redoc
- **MinIO Console:** http://localhost:9001
  - Username: `saramedico_minio_admin`
  - Password: `SaraMed1c0_Min10_2024!SecurePass`
- **MailHog Web UI:** http://localhost:8025

### Development

#### Install dependencies locally (for IDE support)

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### Run tests

```bash
# Inside the container
docker-compose exec backend pytest

# Or locally (if venv activated)
pytest
```

#### Create a new database migration

```bash
docker-compose exec backend alembic revision --autogenerate -m "description"
```

#### Apply migrations

```bash
docker-compose exec backend alembic upgrade head
```

#### View logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
```

### Project Structure

```
backend/
├── alembic/              # Database migrations
│   ├── versions/         # Migration scripts
│   └── env.py           # Alembic environment
├── app/
│   ├── api/             # API routes
│   │   └── v1/          # API version 1
│   ├── core/            # Core functionality (auth, security)
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic
│   ├── utils/           # Utility functions
│   ├── workers/         # Celery tasks
│   ├── config.py        # Configuration
│   ├── database.py      # Database setup
│   └── main.py          # FastAPI app
├── tests/               # Test suite
├── scripts/             # Utility scripts
├── logs/                # Application logs
├── docker-compose.yml   # Docker services
├── Dockerfile           # Backend image
├── requirements.txt     # Python dependencies
└── .env                 # Environment variables
```

### Tech Stack

- **Framework:** FastAPI (async)
- **Database:** PostgreSQL 15 + pgvector
- **ORM:** SQLAlchemy 2.0 (async) + Alembic
- **Cache/Queue:** Redis 7
- **Storage:** MinIO (S3-compatible)
- **Email (Dev):** MailHog
- **Workers:** Celery + Celery Beat
- **Auth:** JWT + bcrypt + TOTP

### API Endpoints (Phase 1)

#### Health Checks

- `GET /health` - Overall system health
- `GET /health/database` - PostgreSQL status
- `GET /health/redis` - Redis status
- `GET /health/minio` - MinIO status

### Development Workflow

1. **Phase-by-phase development** - Each phase must be completed and tested before proceeding
2. **Test-driven** - Write tests for new features
3. **Migrations first** - Always create migrations for schema changes
4. **Code quality** - Use Black, Ruff, and isort for formatting

### Stopping Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (⚠️ deletes all data)
docker-compose down -v
```

### Troubleshooting

#### Backend won't start

```bash
# Check logs
docker-compose logs backend

# Rebuild image
docker-compose build backend
docker-compose up -d
```

#### Database connection errors

```bash
# Check PostgreSQL logs
docker-compose logs postgres

# Verify PostgreSQL is healthy
docker-compose ps postgres
```

#### Can't access MinIO

```bash
# Check MinIO logs
docker-compose logs minio

# Verify buckets were created
docker-compose logs minio-setup
```

### Next Steps

See `DEVELOPMENT_ROADMAP.md` for the complete 9-phase development plan.

**Current Phase:** Phase 1 - Local Development Environment Setup ✅

**Next Phase:** Phase 2 - Authentication & User Management

---

## License

Proprietary - Saramedico Platform
