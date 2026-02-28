#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "========================================="
echo "  AlphaStream India - Local Stop"
echo "========================================="

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Kill from PID file
if [ -f "$PROJECT_DIR/.pids" ]; then
    while IFS= read -r pid; do
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "${YELLOW}Stopping process $pid...${NC}"
            kill "$pid" 2>/dev/null || true
        fi
    done < "$PROJECT_DIR/.pids"
    rm "$PROJECT_DIR/.pids"
fi

# Also kill by port (fallback)
for port in 8000 3000; do
    pid=$(lsof -ti :$port 2>/dev/null || true)
    if [ -n "$pid" ]; then
        echo -e "${YELLOW}Killing process on port $port (PID: $pid)${NC}"
        kill "$pid" 2>/dev/null || true
    fi
done

# Kill celery processes
pkill -f "celery.*alphastream" 2>/dev/null || true

echo -e "${GREEN}All services stopped.${NC}"
