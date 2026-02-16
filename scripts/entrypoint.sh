#!/bin/bash
# =====================================================
# SaraMedico Backend Entrypoint script
# =====================================================

set -e

echo "🚀 Starting SaraMedico Backend Entrypoint..."

# 1. Run migrations and seeding ONLY if starting the backend API
if [[ "$*" == *"uvicorn"* ]]; then
    echo "🔄 Step 1: Running database migrations..."
    bash ./scripts/run-migrations.sh

    echo "🌱 Step 2: Seeding initial data..."
    python scripts/seed_calendar_test_users.py
    
    echo "✅ Backend environment is ready!"
else
    echo "⏳ Waiting for database to be ready (for worker/beat)..."
    while ! pg_isready -h "postgres" -p "5432" -U "saramedico_user" > /dev/null 2>&1; do
        sleep 1
    done
    echo "✅ Database is up, starting worker..."
fi

# 4. Execute the CMD from docker-compose or Dockerfile
echo "🏃 Executing: $@"
exec "$@"
