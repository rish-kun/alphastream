#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

# ── Parse flags ─────────────────────────────────────────────────
DEV_MODE=false
for arg in "$@"; do
    case "$arg" in
        --dev)
            DEV_MODE=true
            ;;
        --help|-h)
            echo "Usage: $0 [--dev]"
            echo ""
            echo "  --dev    Enable development mode (hot-reload, volume mounts)"
            echo "           Layers docker-compose.dev.yml on top of docker-compose.yml"
            echo ""
            echo "Examples:"
            echo "  $0           # production build"
            echo "  $0 --dev     # development with hot-reload"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $arg${NC}"
            echo "Run '$0 --help' for usage."
            exit 1
            ;;
    esac
done

echo "========================================="
echo "  AlphaStream India - Docker Start"
echo "========================================="

if [ "$DEV_MODE" = true ]; then
    echo -e "  Mode: ${CYAN}development${NC} (hot-reload enabled)"
    echo ""
    COMPOSE_CMD=(docker compose -f "$PROJECT_DIR/docker-compose.yml" -f "$PROJECT_DIR/docker-compose.dev.yml")
else
    echo -e "  Mode: ${CYAN}production${NC}"
    echo ""
    COMPOSE_CMD=(docker compose -f "$PROJECT_DIR/docker-compose.yml")
fi

# ── Check prerequisites ─────────────────────────────────────────
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: docker is not installed${NC}"
    exit 1
fi

if ! docker info &> /dev/null 2>&1; then
    echo -e "${RED}Error: Docker daemon is not running${NC}"
    exit 1
fi

# ── Check .env file ──────────────────────────────────────────────
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo -e "${YELLOW}Warning: .env file not found. Copying from .env.example...${NC}"
    cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
    echo -e "${YELLOW}Please review .env and fill in your API keys.${NC}"
fi

# ── Build and start ──────────────────────────────────────────────
echo -e "${CYAN}Building and starting all containers...${NC}"
echo ""
"${COMPOSE_CMD[@]}" up --build -d

echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}  All containers started!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo "  Infrastructure:"
echo "    Postgres: localhost:5433  (container: alphastream-postgres:5432)"
echo "    Redis:    localhost:6380  (container: alphastream-redis:6379)"
echo ""
echo "  Application:"
echo "    Backend:  http://localhost:8000"
echo "    API Docs: http://localhost:8000/docs"
echo "    Frontend: http://localhost:3000"
echo ""
echo "  Useful commands:"
echo "    Logs:     docker compose logs -f"
echo "    Status:   docker compose ps"
echo "    Stop:     ./scripts/stop-docker.sh"
if [ "$DEV_MODE" = true ]; then
    echo ""
    echo -e "  ${CYAN}Dev mode active:${NC} code changes will auto-reload."
fi
echo ""
