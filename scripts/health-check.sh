#!/bin/bash
# =====================================================
# Comprehensive Health Check Script
# Checks all critical services
# =====================================================

set -e

echo "🏥 Running comprehensive health checks..."

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track overall health
all_healthy=true

# Function to check service
check_service() {
    local service_name=$1
    local check_command=$2
    
    echo -n "Checking $service_name... "
    
    if eval "$check_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Healthy${NC}"
        return 0
    else
        echo -e "${RED}❌ Unhealthy${NC}"
        all_healthy=false
        return 1
    fi
}

# 1. Check Database
check_service "PostgreSQL" "pg_isready -h ${DATABASE_HOST:-postgres} -p ${DATABASE_PORT:-5432} -U ${DATABASE_USER:-saramedico_user}"

# 2. Check Redis
check_service "Redis" "redis-cli -h ${REDIS_HOST:-redis} -p ${REDIS_PORT:-6379} -a ${REDIS_PASSWORD:-SaraMed1c0_Redis_2024!SecurePass} ping | grep -q PONG"

# 3. Check MinIO
check_service "MinIO" "curl -f -s http://${MINIO_HOST:-minio}:${MINIO_PORT:-9000}/minio/health/live"

# 4. Check Backend API
check_service "Backend API" "curl -f -s http://${API_HOST:-localhost}:${API_PORT:-8000}/health"

# 5. Check Database Connection (via API)
echo -n "Checking Database connectivity (via API)... "
if curl -f -s "http://${API_HOST:-localhost}:${API_PORT:-8000}/health/database" | grep -q "healthy\|ok\|success"; then
    echo -e "${GREEN}✅ Connected${NC}"
else
    echo -e "${RED}❌ Not Connected${NC}"
    all_healthy=false
fi

# 6. Check Redis Connection (via API)
echo -n "Checking Redis connectivity (via API)... "
if curl -f -s "http://${API_HOST:-localhost}:${API_PORT:-8000}/health/redis" | grep -q "healthy\|ok\|success"; then
    echo -e "${GREEN}✅ Connected${NC}"
else
    echo -e "${YELLOW}⚠️  Not Connected (non-critical)${NC}"
fi

# 7. Check MinIO Connection (via API)
echo -n "Checking MinIO connectivity (via API)... "
if curl -f -s "http://${API_HOST:-localhost}:${API_PORT:-8000}/health/minio" | grep -q "healthy\|ok\|success"; then
    echo -e "${GREEN}✅ Connected${NC}"
else
    echo -e "${YELLOW}⚠️  Not Connected (non-critical)${NC}"
fi

# Summary
echo ""
echo "========================================="
if [ "$all_healthy" = true ]; then
    echo -e "${GREEN}✅ All critical services are healthy!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some services are unhealthy!${NC}"
    exit 1
fi
