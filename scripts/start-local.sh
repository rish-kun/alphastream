#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "========================================="
echo "  AlphaStream India - Local Start"
echo "========================================="
echo ""
echo "  Mode: app runs natively, DB + Redis in Docker"
echo ""

# ── Environment configuration ─────────────────────────────────────
# Colors (defined early for use in early echo statements)
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

# Source .env file to load all configuration
if [ -f "$PROJECT_DIR/.env" ]; then
    echo -e "${CYAN}Loading environment from .env file...${NC}"
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

# ── Prerequisite checks ────────────────────────────────────────
check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo -e "${RED}Error: $1 is not installed${NC}"
        exit 1
    fi
}

check_command docker
check_command uv
check_command bun
check_command python3

# ── Start infrastructure (Postgres + Redis) ────────────────────
echo -e "${CYAN}Starting infrastructure containers...${NC}"
docker compose -f "$PROJECT_DIR/docker-compose.infra.yml" up -d

echo -e "${YELLOW}Waiting for Postgres to be healthy...${NC}"
until docker inspect --format='{{.State.Health.Status}}' alphastream-postgres 2>/dev/null | grep -q "healthy"; do
    sleep 1
done
echo -e "${GREEN}Postgres is ready.${NC}"

echo -e "${YELLOW}Waiting for Redis to be healthy...${NC}"
until docker inspect --format='{{.State.Health.Status}}' alphastream-redis 2>/dev/null | grep -q "healthy"; do
    sleep 1
done
echo -e "${GREEN}Redis is ready.${NC}"

# ── Initialize database schema/data ────────────────────────────
echo -e "${CYAN}Running database migrations...${NC}"
cd "$PROJECT_DIR/backend"

# Ensure backend venv has pip
if [ ! -f ".venv/bin/pip" ]; then
    echo "Creating backend venv with pip..."
    rm -rf .venv
    uv venv --with pip
fi

uv run alembic upgrade head
echo -e "${GREEN}Migrations complete.${NC}"

echo -e "${CYAN}Seeding stock data...${NC}"
uv run python scripts/seed_stocks.py
echo -e "${GREEN}Seed complete.${NC}"

# ── Install ML dependencies and download models ───────────────────
echo -e "${CYAN}Installing ML dependencies for pipeline...${NC}"
cd "$PROJECT_DIR/pipeline"

# Ensure venv has pip (required for spacy and other tools)
# Recreate venv with pip included if it doesn't have it
if [ ! -f ".venv/bin/pip" ]; then
    echo "Recreating venv with pip..."
    rm -rf .venv
    uv venv --with pip
fi

# Install ML extras using uv
uv sync --extra ml
echo -e "${GREEN}ML dependencies installed.${NC}"

echo -e "${CYAN}Downloading spaCy model...${NC}"
# Download spacy model using python directly
.venv/bin/python -m spacy download en_core_web_sm
echo -e "${GREEN}spaCy model downloaded.${NC}"

# ── Start application processes ─────────────────────────────────
echo ""
echo -e "${CYAN}Starting application processes...${NC}"

echo -e "${YELLOW}Starting backend...${NC}"
cd "$PROJECT_DIR/backend"
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo -e "${GREEN}Backend started (PID: $BACKEND_PID)${NC}"

echo -e "${YELLOW}Starting Celery worker...${NC}"
cd "$PROJECT_DIR/pipeline"
uv run celery -A pipeline.celery_app worker --loglevel=info &
CELERY_PID=$!
echo -e "${GREEN}Celery worker started (PID: $CELERY_PID)${NC}"

echo -e "${YELLOW}Starting Celery beat...${NC}"
uv run celery -A pipeline.celery_app beat --loglevel=info &
BEAT_PID=$!
echo -e "${GREEN}Celery beat started (PID: $BEAT_PID)${NC}"

echo -e "${YELLOW}Starting frontend...${NC}"
cd "$PROJECT_DIR/frontend"
bun run dev &
FRONTEND_PID=$!
echo -e "${GREEN}Frontend started (PID: $FRONTEND_PID)${NC}"

# Save PIDs for stop script
echo "$BACKEND_PID" > "$PROJECT_DIR/.pids"
echo "$CELERY_PID" >> "$PROJECT_DIR/.pids"
echo "$BEAT_PID" >> "$PROJECT_DIR/.pids"
echo "$FRONTEND_PID" >> "$PROJECT_DIR/.pids"

echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}  All services started!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo "  Infrastructure (Docker):"
echo "    Postgres: localhost:5433"
echo "    Redis:    localhost:6380"
echo ""
echo "  Application (native):"
echo "    Backend:  http://localhost:8000"
echo "    API Docs: http://localhost:8000/docs"
echo "    Frontend: http://localhost:3000"
echo ""
echo "  Run './scripts/stop-local.sh' to stop all services"
echo ""

# Wait for all background processes
wait
