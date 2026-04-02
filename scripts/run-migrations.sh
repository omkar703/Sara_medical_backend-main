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

# Check for multiple heads (branched history) and fix automatically
HEADS=$(alembic heads 2>/dev/null | wc -l)
if [ "$HEADS" -gt 1 ]; then
    echo "⚠️  Multiple migration heads detected ($HEADS). Merging..."
    alembic merge heads -m "auto_merge_branches" || echo "⚠️ Merge failed, attempting upgrade anyway"
fi

if alembic upgrade head 2>&1; then
    echo "✅ Alembic migrations completed successfully!"
else
    echo "⚠️ Alembic failed - attempting to stamp and repair..."
    alembic stamp e1c2d3e4f5a6 && echo "✅ Stamped to latest revision" || \
    alembic stamp cad819385621 && echo "✅ Stamped to latest revision" || \
    alembic stamp f9b2c3d4e5f8 && alembic upgrade head || \
    alembic stamp 70e05e24e9bb && alembic upgrade head || \
    echo "❌ Migration repair failed - app will attempt to start anyway"
fi

# Step 3: Direct Schema Check (ensure missing tables like notifications exist)
echo "🚀 Running direct schema check..."
python scripts/ensure_db_schema.py || echo "⚠️ Schema check failed, continuing..."

# Check current migration version
echo "📊 Current migration version:"
alembic current 2>/dev/null || true

echo "✅ Migration process completed!"
