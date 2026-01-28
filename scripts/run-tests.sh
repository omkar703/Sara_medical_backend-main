#!/bin/bash
# =====================================================
# Test Runner Script
# Sets up test environment and runs all tests
# =====================================================

set -e

echo "🧪 Starting test suite..."

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Set test environment
export APP_ENV=testing
export DATABASE_URL="${TEST_DATABASE_URL:-postgresql+asyncpg://saramedico_user:SaraMed1c0_Dev_2024!Secure@localhost:5435/saramedico_test}"

# Create test database if it doesn't exist
echo "📦 Setting up test database..."
PGPASSWORD="${DATABASE_PASSWORD:-SaraMed1c0_Dev_2024!Secure}" psql -h "${DATABASE_HOST:-localhost}" -p "${DATABASE_PORT:-5435}" -U "${DATABASE_USER:-saramedico_user}" -d postgres -c "CREATE DATABASE saramedico_test;" 2>/dev/null || echo "Test database already exists"

# Enable extensions on test database
echo "🔧 Enabling PostgreSQL extensions..."
PGPASSWORD="${DATABASE_PASSWORD:-SaraMed1c0_Dev_2024!Secure}" psql -h "${DATABASE_HOST:-localhost}" -p "${DATABASE_PORT:-5435}" -U "${DATABASE_USER:-saramedico_user}" -d saramedico_test <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS "pg_trgm";
    CREATE EXTENSION IF NOT EXISTS "vector";
EOSQL

echo ""
echo "========================================="
echo "Running Test Suite"
echo "========================================="
echo ""

# Run health check tests first
echo -e "${YELLOW}📋 Running Health Check Tests...${NC}"
pytest tests/test_health.py -v --tb=short || true

# Run authentication tests
echo ""
echo -e "${YELLOW}📋 Running Authentication Tests...${NC}"
pytest tests/test_auth_simple.py -v --tb=short || true

# Run endpoint tests
echo ""
echo -e "${YELLOW}📋 Running Endpoint Tests...${NC}"
pytest tests/test_complete_endpoints.py -v --tb=short || true

# Run E2E tests
echo ""
echo -e "${YELLOW}📋 Running End-to-End Tests...${NC}"
pytest tests/test_e2e_complete_flow.py -v --tb=short || true

# Run all other tests
echo ""
echo -e "${YELLOW}📋 Running Additional Tests...${NC}"
pytest tests/ -v --tb=short \
    --ignore=tests/test_health.py \
    --ignore=tests/test_auth_simple.py \
    --ignore=tests/test_complete_endpoints.py \
    --ignore=tests/test_e2e_complete_flow.py \
    || true

# Generate coverage report
echo ""
echo "========================================="
echo "Generating Coverage Report"
echo "========================================="
echo ""

pytest tests/ --cov=app --cov-report=term-missing --cov-report=html || true

echo ""
echo "========================================="
if [ -f htmlcov/index.html ]; then
    echo -e "${GREEN}✅ Coverage report generated: htmlcov/index.html${NC}"
else
    echo -e "${YELLOW}⚠️  Coverage report not generated${NC}"
fi
echo "========================================="

# Cleanup
echo ""
echo "🧹 Cleaning up test database..."
# Optionally drop test database
# PGPASSWORD="${DATABASE_PASSWORD:-SaraMed1c0_Dev_2024!Secure}" psql -h "${DATABASE_HOST:-localhost}" -p "${DATABASE_PORT:-5435}" -U "${DATABASE_USER:-saramedico_user}" -d postgres -c "DROP DATABASE IF EXISTS saramedico_test;"

echo -e "${GREEN}✅ Test suite completed!${NC}"
