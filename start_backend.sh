#!/bin/bash
# Script to start backend services with proper Docker permissions

# Change to backend directory
cd /home/op/Videos/saramedico/backend

# Start Docker Compose services
sg docker -c "docker compose up -d"

# Show status
sg docker -c "docker compose ps"
