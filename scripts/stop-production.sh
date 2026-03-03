#!/usr/bin/env bash
# Stop AlphaStream production deployment

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
log_warn() { echo -e "${YELLOW}$1${NC}"; }

echo "========================================="
echo "  Stopping AlphaStream Production"
echo "========================================="
echo ""

# Stop nginx
log_info "Stopping nginx..."
systemctl stop nginx 2>/dev/null || true
log_success "✓ nginx stopped"

# Kill application processes
log_info "Stopping application processes..."

if [ -f "$PROJECT_DIR/.pids" ]; then
    while read -r pid; do
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
            log_success "✓ Stopped process $pid"
        fi
    done < "$PROJECT_DIR/.pids"
    rm "$PROJECT_DIR/.pids"
fi

# Fallback: kill any remaining processes
pkill -f "uvicorn" 2>/dev/null || true
pkill -f "celery" 2>/dev/null || true
pkill -f "next" 2>/dev/null || true

log_success "✓ Application processes stopped"

# Stop Docker infrastructure
log_info "Stopping Docker infrastructure..."
cd "$PROJECT_DIR"
docker compose -f docker-compose.infra.yml down
log_success "✓ Infrastructure stopped"

echo ""
echo "========================================="
log_success "  All services stopped"
echo "========================================="
