#!/bin/bash

# Simple wrapper to start backend with newgrp
# Run this in a terminal: bash start_with_docker.sh

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "====================================="
echo "Starting Saramedico Backend Services"
echo "====================================="
echo ""

# Try to use newgrp to switch to docker group and run docker compose
bash -c "newgrp docker << 'DOCKERCMD'
cd $SCRIPT_DIR
echo 'Checking current Docker status...'
docker compose ps -a
echo ''
echo 'Starting all services...'
docker compose up -d
echo ''
echo 'Waiting for services to start...'
sleep 5
echo ''
echo 'Service status:'
docker compose ps
echo ''
echo 'Backend should be available at: http://localhost:8000'
echo 'API Documentation: http://localhost:8000/docs'
echo ''
echo 'To view logs: docker compose logs -f'
DOCKERCMD
"

