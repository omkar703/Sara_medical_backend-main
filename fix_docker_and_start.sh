#!/bin/bash

# Helper script to fix Docker permissions and start Saramedico backend
# This script needs to be run with sudo

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "==================================="
echo "Saramedico Backend Setup Script"
echo "==================================="
echo ""

# Check if running as root/sudo
if [ "$EUID" -ne 0 ]; then 
   echo "ERROR: Please run this script with sudo:"
   echo "  sudo $0"
   exit 1
fi

# Get the actual user (not root when using sudo)
ACTUAL_USER=${SUDO_USER:-$USER}
echo "Adding user '$ACTUAL_USER' to docker group..."

# Add user to docker group
usermod -aG docker $ACTUAL_USER

echo "✅ User added to docker group"
echo ""
echo "IMPORTANT: You need to log out and log back in (or restart) for group changes to take effect."
echo ""
echo "After logging back in, run this command to start the backend:"
echo "  cd $SCRIPT_DIR"
echo "  docker compose up -d"
echo ""
echo "Or if you want to continue in this session, run:"
echo "  newgrp docker"
echo "  cd $SCRIPT_DIR"
echo "  docker compose up -d"

