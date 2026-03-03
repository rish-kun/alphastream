#!/usr/bin/env bash
# AlphaStream Production Deployment Script
# Deploys with native app processes + nginx + SSL
# Domain: alphastream.wallstreetbitsp.org

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DOMAIN="alphastream.wallstreetbitsp.org"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info() { echo -e "${CYAN}$1${NC}"; }
log_success() { echo -e "${GREEN}$1${NC}"; }
log_error() { echo -e "${RED}$1${NC}"; }
log_warn() { echo -e "${YELLOW}$1${NC}"; }

# Check if running as root for certbot
if [ "$EUID" -ne 0 ]; then
    log_error "Please run as root or with sudo for SSL certificate management"
    exit 1
fi

echo "========================================="
echo "  AlphaStream Production Deployment"
echo "  Domain: $DOMAIN"
echo "========================================="
echo ""

# ── Step 1: Pre-deployment checks ─────────────────────────────
log_info "=== Step 1: Pre-deployment Checks ==="

# Check prerequisites
for cmd in docker uv bun python3 nginx certbot; do
    if ! command -v "$cmd" &> /dev/null; then
        log_error "Error: $cmd is not installed"
        exit 1
    fi
    log_success "✓ $cmd found"
done

# Check Docker daemon
if ! docker info > /dev/null 2>&1; then
    log_error "Docker daemon is not running"
    exit 1
fi
log_success "✓ Docker daemon is running"

# Check .env exists and has required variables
if [ ! -f "$PROJECT_DIR/.env" ]; then
    log_error ".env file not found"
    exit 1
fi

# Source .env for validation
set -a
source "$PROJECT_DIR/.env"
set +a

# Verify critical variables
REQUIRED_VARS=("SECRET_KEY" "GEMINI_API_KEYS" "DATABASE_URL" "REDIS_URL")
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var:-}" ]; then
        log_error "Missing required env variable: $var"
        exit 1
    fi
done
log_success "✓ Environment variables validated"

# ── Step 2: Setup production .env ─────────────────────────────
log_info "=== Step 2: Configuring Production Environment ==="

# Backup original .env
cp "$PROJECT_DIR/.env" "$PROJECT_DIR/.env.backup.$(date +%Y%m%d_%H%M%S)"

# Update .env for production if needed
if ! grep -q "^NEXT_PUBLIC_API_URL=https://$DOMAIN" "$PROJECT_DIR/.env"; then
    log_info "Updating API URLs for production..."
    sed -i "s|^NEXT_PUBLIC_API_URL=.*|NEXT_PUBLIC_API_URL=https://$DOMAIN/api/v1|" "$PROJECT_DIR/.env"
    sed -i "s|^NEXT_PUBLIC_WS_URL=.*|NEXT_PUBLIC_WS_URL=wss://$DOMAIN/api/v1|" "$PROJECT_DIR/.env"
    sed -i "s|^CORS_ORIGINS=.*|CORS_ORIGINS=[\"https://$DOMAIN\"]|" "$PROJECT_DIR/.env"
    log_success "✓ Updated .env for production"
fi

# ── Step 3: SSL Certificates ──────────────────────────────────
log_info "=== Step 3: SSL Certificate Setup ==="

# Create certbot webroot
mkdir -p /var/www/certbot

# Check if certificates exist
if [ -d "/etc/letsencrypt/live/$DOMAIN" ]; then
    log_success "✓ SSL certificates already exist"
    # Check if renewal is needed
    expiry=$(openssl x509 -enddate -noout -in "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" | cut -d= -f2)
    log_info "  Certificate expires: $expiry"
else
    log_info "Obtaining SSL certificates from Let's Encrypt..."
    
    # Stop any service using port 80
    systemctl stop nginx 2>/dev/null || true
    
    # Obtain certificate
    certbot certonly --standalone \
        --preferred-challenges http \
        --agree-tos \
        --non-interactive \
        --email admin@$DOMAIN \
        -d $DOMAIN
    
    log_success "✓ SSL certificates obtained"
fi

# Setup auto-renewal cron job
if ! crontab -l 2>/dev/null | grep -q "certbot renew"; then
    log_info "Setting up certificate auto-renewal..."
    (crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet --deploy-hook 'systemctl reload nginx'") | crontab -
    log_success "✓ Auto-renewal cron job added"
fi

# ── Step 4: Configure nginx ───────────────────────────────────
log_info "=== Step 4: nginx Configuration ==="

# Copy nginx config
if [ -f "$PROJECT_DIR/nginx/nginx.conf" ]; then
    cp "$PROJECT_DIR/nginx/nginx.conf" /etc/nginx/nginx.conf
    
    # Replace domain placeholder if exists
    sed -i "s/alphastream.wallstreetbitsp.org/$DOMAIN/g" /etc/nginx/nginx.conf
    
    # Test nginx configuration
    if nginx -t; then
        log_success "✓ nginx configuration is valid"
    else
        log_error "✗ nginx configuration test failed"
        exit 1
    fi
else
    log_error "nginx.conf not found in $PROJECT_DIR/nginx/"
    exit 1
fi

# ── Step 5: Start Infrastructure ──────────────────────────────
log_info "=== Step 5: Starting Docker Infrastructure ==="

cd "$PROJECT_DIR"

# Stop any existing containers
docker compose -f docker-compose.infra.yml down 2>/dev/null || true

# Start Postgres and Redis with memory limits
docker compose -f docker-compose.infra.yml up -d

# Wait for health checks
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

# ── Step 6: Database Setup ────────────────────────────────────
log_info "=== Step 6: Database Setup ==="

cd "$PROJECT_DIR/backend"

# Run migrations
log_info "Running database migrations..."
uv run alembic upgrade head
log_success "✓ Migrations complete"

# Seed data
log_info "Seeding stock data..."
uv run python scripts/seed_stocks.py
log_success "✓ Seed complete"

# ── Step 7: Start Application ─────────────────────────────────
log_info "=== Step 7: Starting Application ==="

# Stop any existing processes
pkill -f "uvicorn" 2>/dev/null || true
pkill -f "celery" 2>/dev/null || true
pkill -f "next" 2>/dev/null || true
sleep 2

# Build frontend for production
log_info "Building frontend for production..."
cd "$PROJECT_DIR/frontend"
bun run build
log_success "✓ Frontend built"

# Start backend
log_info "Starting backend..."
cd "$PROJECT_DIR/backend"
nohup uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2 > /var/log/alphastream-backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > "$PROJECT_DIR/.pids"
log_success "✓ Backend started (PID: $BACKEND_PID)"

# Start Celery worker
log_info "Starting Celery worker..."
cd "$PROJECT_DIR/pipeline"
nohup uv run celery -A pipeline.celery_app worker --loglevel=info --concurrency=1 --prefetch-multiplier=1 > /var/log/alphastream-worker.log 2>&1 &
WORKER_PID=$!
echo $WORKER_PID >> "$PROJECT_DIR/.pids"
log_success "✓ Celery worker started (PID: $WORKER_PID)"

# Start Celery beat
log_info "Starting Celery beat scheduler..."
nohup uv run celery -A pipeline.celery_app beat --loglevel=info > /var/log/alphastream-beat.log 2>&1 &
BEAT_PID=$!
echo $BEAT_PID >> "$PROJECT_DIR/.pids"
log_success "✓ Celery beat started (PID: $BEAT_PID)"

# Start frontend (production mode)
log_info "Starting frontend..."
cd "$PROJECT_DIR/frontend"
nohup bun run start > /var/log/alphastream-frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID >> "$PROJECT_DIR/.pids"
log_success "✓ Frontend started (PID: $FRONTEND_PID)"

# ── Step 8: Start nginx ───────────────────────────────────────
log_info "=== Step 8: Starting nginx ==="

systemctl start nginx
systemctl enable nginx

if systemctl is-active --quiet nginx; then
    log_success "✓ nginx started and enabled"
else
    log_error "✗ nginx failed to start"
    exit 1
fi

# ── Step 9: Health Checks ─────────────────────────────────────
log_info "=== Step 9: Health Verification ==="

sleep 5

# Check backend
if curl -sf http://127.0.0.1:8000/api/v1/health > /dev/null; then
    log_success "✓ Backend is responding"
else
    log_warn "⚠ Backend health check failed"
fi

# Check frontend
if curl -sf http://127.0.0.1:3000 > /dev/null; then
    log_success "✓ Frontend is responding"
else
    log_warn "⚠ Frontend health check failed"
fi

# Check HTTPS
if curl -sf https://$DOMAIN/health > /dev/null; then
    log_success "✓ HTTPS endpoint is responding"
else
    log_warn "⚠ HTTPS health check failed (may need a moment)"
fi

# ── Step 10: Final Status ─────────────────────────────────────
echo ""
echo "========================================="
log_success "  Deployment Complete!"
echo "========================================="
echo ""
echo "  Domain: https://$DOMAIN"
echo "  Health: https://$DOMAIN/health"
echo "  API:    https://$DOMAIN/api/v1"
echo "  Docs:   https://$DOMAIN/docs"
echo ""
echo "  Logs:"
echo "    Backend:  /var/log/alphastream-backend.log"
echo "    Worker:   /var/log/alphastream-worker.log"
echo "    Beat:     /var/log/alphastream-beat.log"
echo "    Frontend: /var/log/alphastream-frontend.log"
echo "    nginx:    /var/log/nginx/access.log"
echo ""
echo "  Management:"
echo "    View status: systemctl status nginx"
echo "    View logs:   tail -f /var/log/alphastream-*.log"
echo "    Stop app:    $PROJECT_DIR/scripts/stop-production.sh"
echo "    Restart:     $PROJECT_DIR/scripts/deploy-production.sh"
echo ""
