#!/bin/bash

# Script to monitor backend logs
# Usage: sudo ./watch_logs.sh [service_name]
# Default service: backend
# Available services: backend, postgres, redis, minio, mailhog, celery_worker, celery_beat

SERVICE=${1:-backend}

cd /home/op/Videos/saramedico/backend

echo "======================================"
echo "   Monitoring ${SERVICE} logs"
echo "======================================"
echo "Press Ctrl+C to stop"
echo ""

# Follow logs in real-time
docker compose logs -f --tail=100 ${SERVICE}
