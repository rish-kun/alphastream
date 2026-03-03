#!/usr/bin/env bash
# AlphaStream Backend-Only Deployment Script
# Deploys only infrastructure (PostgreSQL, Redis) and FastAPI backend

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info() { echo -e "${CYAN}$1${NC}"; }
log_success() { echo -e "${GREEN}$1${NC}"; }
log_error() { echo -e "${RED}$1${NC}"; }
log_warn() { echo -e "${YELLOW}$1${NC}"; }

echo "========================================="
echo "  AlphaStream Backend-Only Deployment"
echo "========================================="
echo ""

# ── Step 1: Pre-deployment checks ─────────────────────────────
log_info "=== Step 1: Pre-deployment Checks ==="

for cmd in docker uv python3; do
    if ! command -v "$cmd" &> /dev/null; then
        log_error "Error: $cmd is not installed"
        exit 1
    fi
    log_success "✓ $cmd found"
done

if ! docker info > /dev/null 2>&1; then
    log_error "Docker daemon is not running"
    exit 1
fi
log_success "✓ Docker daemon is running"

if [ ! -f "$PROJECT_DIR/.env" ]; then
    log_error ".env file not found"
    exit 1
fi

set -a
source "$PROJECT_DIR/.env"
set +a

REQUIRED_VARS=("SECRET_KEY" "DATABASE_URL" "REDIS_URL")
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var:-}" ]; then
        log_error "Missing required env variable: $var"
        exit 1
    fi
done
log_success "✓ Environment variables validated"

# ── Step 2: Start Infrastructure ──────────────────────────────
log_info "=== Step 2: Starting Docker Infrastructure ==="

cd "$PROJECT_DIR"

docker compose -f docker-compose.infra.yml down 2>/dev/null || true

docker compose -f docker-compose.infra.yml up -d

log_info "Waiting for infrastructure to be healthy..."
max_wait=60
count=0
postgres_healthy=false
redis_healthy=false

while [ $count -lt $max_wait ]; do
    if ! $postgres_healthy; then
        if docker inspect --format='{{.State.Health.Status}}' alphastream-postgres 2>/dev/null | grep -q "healthy"; then
            postgres_healthy=true
            log_success "✓ PostgreSQL is healthy"
        fi
    fi
    
    if ! $redis_healthy; then
        if docker inspect --format='{{.State.Health.Status}}' alphastream-redis 2>/dev/null | grep -q "healthy"; then
            redis_healthy=true
            log_success "✓ Redis is healthy"
        fi
    fi
    
    if $postgres_healthy && $redis_healthy; then
        break
    fi
    
    sleep 2
    ((count++))
    echo -n "."
done
echo ""

if ! $postgres_healthy || ! $redis_healthy; then
    log_error "Infrastructure failed to become healthy"
    exit 1
fi

# ── Step 3: Database Setup ────────────────────────────────────
log_info "=== Step 3: Database Setup ==="

cd "$PROJECT_DIR/backend"

log_info "Running database migrations..."
uv run alembic upgrade head
log_success "✓ Migrations complete"

# ── Step 4: Start Backend ────────────────────────────────────
log_info "=== Step 4: Starting Backend ==="

pkill -f "uvicorn" 2>/dev/null || true
sleep 2

log_info "Starting backend..."
cd "$PROJECT_DIR/backend"
nohup uv run uvicorn app.main:app --host 127.0.0.1 --port 8001 --workers 2 > /var/log/alphastream-backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > "$PROJECT_DIR/.pids.backend"
log_success "✓ Backend started (PID: $BACKEND_PID)"

# ── Step 5: Health Check ─────────────────────────────────────
log_info "=== Step 5: Health Verification ==="

sleep 5

if curl -sf http://127.0.0.1:8001/api/v1/health > /dev/null; then
    log_success "✓ Backend is responding"
else
    log_warn "⚠ Backend health check failed"
fi

# ── Step 6: Final Status ─────────────────────────────────────
echo ""
echo "========================================="
log_success "  Backend Deployment Complete!"
echo "========================================="
echo ""
echo "  Backend:  http://127.0.0.1:8001"
echo "  API:      http://127.0.0.1:8001/api/v1"
echo "  Docs:     http://127.0.0.1:8001/docs"
echo ""
echo "  Logs:"
echo "    Backend: /var/log/alphastream-backend.log"
echo ""
echo "  Management:"
echo "    View logs:   tail -f /var/log/alphastream-backend.log"
echo "    Stop:        $PROJECT_DIR/scripts/stop-backend-only.sh"
echo ""
