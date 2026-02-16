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

#### Calendar System 📅

The Calendar System provides Google Calendar-like functionality for all user roles with automatic synchronization.

**Features:**
- ✅ Role-agnostic API (works for patients, doctors, admins, hospitals)
- ✅ Bidirectional appointment sync (creates events for both patient and doctor)
- ✅ Automatic task sync (tasks with due dates appear in calendar)
- ✅ Custom events (user-created calendar entries)
- ✅ Day/Month views with event summaries
- ✅ Color-coded events and reminders

**Endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/calendar/events` | List calendar events (with filters) |
| GET | `/api/v1/calendar/events/{id}` | Get single event details |
| POST | `/api/v1/calendar/events` | Create custom event |
| PUT | `/api/v1/calendar/events/{id}` | Update custom event |
| DELETE | `/api/v1/calendar/events/{id}` | Delete custom event |
| GET | `/api/v1/calendar/day/{date}` | Get day view (YYYY-MM-DD) |
| GET | `/api/v1/calendar/month/{year}/{month}` | Get month summary |

**Query Parameters (GET /events):**
- `start_date` (required) - Start of date range (ISO 8601)
- `end_date` (required) - End of date range (ISO 8601)
- `event_type` (optional) - Filter by type: `appointment`, `custom`, or `task`

**Event Types:**
- **Appointment** 🔵 (Blue `#3B82F6`) - Auto-synced from appointment system
- **Task** 🔴/🟠 (Red/Orange) - Auto-synced from tasks with due dates
- **Custom** 🎨 (User-defined color) - User-created events

**Automatic Sync Behavior:**
1. **Patient books appointment** → Calendar events created for patient AND doctor
2. **Appointment approved** → Both calendar events updated with confirmed time + Zoom link
3. **Appointment cancelled** → Both calendar events marked as cancelled
4. **Task created with due_date** → Calendar event created
5. **Task due_date removed** → Calendar event deleted

**Example Request:**
```bash
# Get all events for next 7 days
curl -X GET "http://localhost:8000/api/v1/calendar/events?start_date=2026-02-16T00:00:00Z&end_date=2026-02-23T23:59:59Z" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Create custom event
curl -X POST "http://localhost:8000/api/v1/calendar/events" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Team Meeting",
    "description": "Weekly sync",
    "start_time": "2026-02-20T14:00:00Z",
    "end_time": "2026-02-20T15:00:00Z",
    "color": "#10B981",
    "reminder_minutes": 15
  }'
```

See full API docs at http://localhost:8000/docs
- **API Guide:** [docs/CALENDAR_API_GUIDE.md](docs/CALENDAR_API_GUIDE.md)
- **Test Report:** [docs/CALENDAR_TEST_REPORT.md](docs/CALENDAR_TEST_REPORT.md)

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
