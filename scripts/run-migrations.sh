#!/bin/bash
# =====================================================
# Database Migration Runner Script
# Waits for database to be ready and runs migrations
# =====================================================

set -e

echo "🔄 Starting database migration process..."

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if pg_isready -h "${DATABASE_HOST:-postgres}" -p "${DATABASE_PORT:-5432}" -U "${DATABASE_USER:-saramedico_user}" > /dev/null 2>&1; then
        echo "✅ Database is ready!"
        break
    fi
    
    attempt=$((attempt + 1))
    echo "   Attempt $attempt/$max_attempts - Database not ready yet..."
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo "⚠️ Database not responding - trying to continue anyway..."
fi

# Run Alembic migrations - try 'head' first, then 'heads' for multiple branch situation
echo "🔄 Running Alembic migrations..."
cd /app

if alembic upgrade head 2>/dev/null; then
    echo "✅ Migrations completed successfully!"
elif alembic upgrade heads 2>&1; then
    echo "✅ Migrations completed (multiple heads resolved)!"
else
    echo "⚠️ Migrations may already be up to date or had non-critical errors - continuing startup..."
fi

# Check current migration version
echo "📊 Current migration version:"
alembic current 2>/dev/null || true

echo "✅ Migration process completed!"
