#!/bin/bash
# Script to start backend services with proper Docker permissions

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Start Docker Compose services
sg docker -c "docker compose up -d"

# Show status
sg docker -c "docker compose ps"

