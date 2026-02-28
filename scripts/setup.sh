#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "========================================="
echo "  AlphaStream India - First Time Setup"
echo "========================================="

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check prerequisites
check_command() {
    if command -v "$1" &> /dev/null; then
        echo -e "${GREEN}✓ $1 found${NC}"
    else
        echo -e "${RED}✗ $1 not found - please install it${NC}"
        exit 1
    fi
}

echo "Checking prerequisites..."
check_command python3
check_command uv
check_command bun
check_command node

# Create .env if not exists
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo -e "${YELLOW}Creating .env from .env.example...${NC}"
    cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
    echo -e "${GREEN}✓ .env created. Please edit it with your API keys.${NC}"
else
    echo -e "${GREEN}✓ .env already exists${NC}"
fi

# Install backend dependencies
echo -e "${YELLOW}Installing backend dependencies...${NC}"
cd "$PROJECT_DIR/backend"
uv sync
echo -e "${GREEN}✓ Backend dependencies installed${NC}"

# Install pipeline dependencies
echo -e "${YELLOW}Installing pipeline dependencies...${NC}"
cd "$PROJECT_DIR/pipeline"
uv sync
echo -e "${GREEN}✓ Pipeline dependencies installed${NC}"

# Install frontend dependencies
echo -e "${YELLOW}Installing frontend dependencies...${NC}"
cd "$PROJECT_DIR/frontend"
bun install
echo -e "${GREEN}✓ Frontend dependencies installed${NC}"

# Download spaCy model
echo -e "${YELLOW}Downloading spaCy model...${NC}"
cd "$PROJECT_DIR/pipeline"
uv run python -m spacy download en_core_web_sm || echo -e "${YELLOW}⚠ spaCy model download failed - you can do this later${NC}"

echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}  Setup complete!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo "  Next steps:"
echo "  1. Edit .env with your API keys"
echo "  2. Start PostgreSQL and Redis (or use docker-compose up)"
echo "  3. Run database migrations: cd backend && uv run alembic upgrade head"
echo "  4. Start the app: ./scripts/start-local.sh"
