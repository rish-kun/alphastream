#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# ── Parse flags ─────────────────────────────────────────────────
WIPE_VOLUMES=false
for arg in "$@"; do
    case "$arg" in
        --volumes|-v)
            WIPE_VOLUMES=true
            ;;
        --help|-h)
            echo "Usage: $0 [--volumes|-v]"
            echo ""
            echo "  --volumes, -v    Also remove named volumes (wipes all data)"
            echo ""
            echo "Examples:"
            echo "  $0              # stop containers, keep data"
            echo "  $0 --volumes    # stop containers and wipe data"
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
echo "  AlphaStream India - Docker Stop"
echo "========================================="

if [ "$WIPE_VOLUMES" = true ]; then
    echo -e "${YELLOW}Stopping all containers and removing volumes...${NC}"
    docker compose -f "$PROJECT_DIR/docker-compose.yml" down -v
    echo -e "${YELLOW}All data volumes have been removed.${NC}"
else
    echo -e "${YELLOW}Stopping all containers (data volumes preserved)...${NC}"
    docker compose -f "$PROJECT_DIR/docker-compose.yml" down
fi

echo ""
echo -e "${GREEN}All containers stopped.${NC}"
