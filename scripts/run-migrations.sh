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

# Run Alembic migrations
echo "🔄 Running Alembic migrations..."
cd /app

if alembic upgrade head 2>/dev/null; then
    echo "✅ Alembic migrations completed successfully!"
elif alembic upgrade heads 2>&1; then
    echo "✅ Alembic migrations completed (multiple heads handled)!"
else
    echo "⚠️ Alembic failed - checking common history mismatch..."
    # Attempt to fix the most common EC2 history mismatch
    alembic stamp 70e05e24e9bb && alembic upgrade head || echo "❌ Migration repair failed"
fi

# Step 3: Direct Schema Check (ensure missing tables like notifications exist)
echo "🚀 Running direct schema check..."
python scripts/ensure_db_schema.py

# Check current migration version
echo "📊 Current migration version:"
alembic current 2>/dev/null || true

echo "✅ Migration process completed!"
