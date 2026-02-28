#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "========================================="
echo "  AlphaStream India - Local Start"
echo "========================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check prerequisites
check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo -e "${RED}Error: $1 is not installed${NC}"
        exit 1
    fi
}

check_command uv
check_command bun
check_command python3

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
echo "  Backend:  http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo "  Frontend: http://localhost:3000"
echo ""
echo "  Run './scripts/stop-local.sh' to stop all services"
echo ""

# Wait for all background processes
wait
