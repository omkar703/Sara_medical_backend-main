#!/bin/bash
# Quick Start Script for Medical OCR Backend

set -e

echo "🏥 Medical OCR Backend - Quick Start"
echo "===================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

echo "✓ Docker found"

# Check if Docker Compose is available
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    echo "❌ Docker Compose not found. Please install Docker Compose."
    exit 1
fi

echo "✓ Docker Compose found"
echo ""

# Build and start services
echo "🔨 Building Docker images..."
$DOCKER_COMPOSE build

echo ""
echo "🚀 Starting services..."
$DOCKER_COMPOSE up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service status
echo ""
echo "📊 Service Status:"
$DOCKER_COMPOSE ps

echo ""
echo "✅ Medical OCR Backend is running!"
echo ""
echo "🌐 Access Points:"
echo "  - API:            http://localhost:8000"
echo "  - API Docs:       http://localhost:8000/docs"
echo "  - ReDoc:          http://localhost:8000/redoc"
echo "  - Flower Monitor: http://localhost:5555"
echo ""
echo "🧪 Test the API:"
echo "  curl http://localhost:8000/health | jq"
echo ""
echo "📝 View logs:"
echo "  $DOCKER_COMPOSE logs -f api"
echo "  $DOCKER_COMPOSE logs -f worker"
echo ""
echo "🛑 Stop services:"
echo "  $DOCKER_COMPOSE down"
echo ""
