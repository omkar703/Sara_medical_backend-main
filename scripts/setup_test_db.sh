#!/bin/bash
# scripts/setup_test_db.sh
# THIS SCRIPT SHOULD BE RUN INSIDE THE BACKEND CONTAINER

echo "Initializing Test Database..."

# Use environment variables already present in the container
DB_USER=${DATABASE_USER:-saramedico_user}
DB_PASS=${DATABASE_PASSWORD:-SaraMed1c0_Dev_2024!Secure}
DB_NAME_TEST="saramedico_test"
DB_HOST="postgres"

echo "Creating database $DB_NAME_TEST..."
PGPASSWORD=$DB_PASS psql -h $DB_HOST -U $DB_USER -d postgres -c "CREATE DATABASE $DB_NAME_TEST;" || echo "Database might already exist"

echo "Enabling PGVector extension in $DB_NAME_TEST..."
PGPASSWORD=$DB_PASS psql -h $DB_HOST -U $DB_USER -d $DB_NAME_TEST -c "CREATE EXTENSION IF NOT EXISTS vector;"

echo "Running migrations on $DB_NAME_TEST..."
export DATABASE_URL="postgresql+asyncpg://$DB_USER:$DB_PASS@$DB_HOST:5432/$DB_NAME_TEST"
alembic upgrade head

echo "Test database setup successfully!"
