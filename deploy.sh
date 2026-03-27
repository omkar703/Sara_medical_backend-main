#!/bin/bash
# =====================================================
# SARAMEDICO - EC2 DEPLOYMENT SCRIPT
# Builds and starts both frontend + backend services
# =====================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================="
echo "  🏥 SaraMedico EC2 Deployment"
echo "============================================="

# ── 1. Verify Docker is available ──────────────────
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not available. Please install docker-compose-plugin."
    exit 1
fi

echo "✅ Docker $(docker --version | grep -oP '\d+\.\d+\.\d+') is available"

# ── 2. Verify frontend directory exists ────────────
FRONTEND_PATH="${FRONTEND_PATH:-../saramedico-deploy}"
if [ ! -d "$FRONTEND_PATH" ]; then
    echo "❌ Frontend directory not found at: $FRONTEND_PATH"
    echo "   Set FRONTEND_PATH env var or ensure the directory exists."
    exit 1
fi
echo "✅ Frontend found at: $FRONTEND_PATH"

# ── 3. Verify required config files exist ──────────
for f in .env Dockerfile docker-compose.yml nginx/default.conf; do
    if [ ! -f "$f" ]; then
        echo "❌ Required file missing: $f"
        exit 1
    fi
done
echo "✅ All backend config files present"

for f in "$FRONTEND_PATH/Dockerfile" "$FRONTEND_PATH/package.json"; do
    if [ ! -f "$f" ]; then
        echo "❌ Required frontend file missing: $f"
        exit 1
    fi
done
echo "✅ All frontend config files present"

# ── 4. Stop existing containers ───────────────────
echo ""
echo "🛑 Stopping existing containers..."
docker compose down --remove-orphans 2>/dev/null || true

# ── 5. Build all images ──────────────────────────
echo ""
echo "🔨 Building Docker images (this may take a few minutes)..."
docker compose build --no-cache

# ── 6. Start all services ────────────────────────
echo ""
echo "🚀 Starting all services..."
docker compose up -d

# ── 7. Wait and show status ──────────────────────
echo ""
echo "⏳ Waiting for services to start..."
sleep 10

echo ""
echo "============================================="
echo "  📊 Service Status"
echo "============================================="
docker compose ps

echo ""
echo "============================================="
echo "  🎉 Deployment Complete!"
echo "============================================="
echo ""
echo "  🌐 Frontend:   http://$(curl -s ifconfig.me 2>/dev/null || echo '<EC2_PUBLIC_IP>'):80"
echo "  🔧 Backend API: http://$(curl -s ifconfig.me 2>/dev/null || echo '<EC2_PUBLIC_IP>'):80/api/v1"
echo "  📖 API Docs:    http://$(curl -s ifconfig.me 2>/dev/null || echo '<EC2_PUBLIC_IP>'):80/docs"
echo "  📧 MailHog:     http://$(curl -s ifconfig.me 2>/dev/null || echo '<EC2_PUBLIC_IP>'):8030"
echo "  📦 MinIO:       http://$(curl -s ifconfig.me 2>/dev/null || echo '<EC2_PUBLIC_IP>'):9011"
echo ""
echo "  📝 View logs:   docker compose logs -f"
echo "  📝 Backend log: docker compose logs -f backend"
echo "  📝 Frontend log: docker compose logs -f frontend"
echo ""
