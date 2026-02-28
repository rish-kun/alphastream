#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "========================================="
echo "  AlphaStream India - Seed Database"
echo "========================================="

echo "Running database migrations..."
cd "$PROJECT_DIR/backend"
uv run alembic upgrade head

echo "Seeding stock data..."
uv run python -c "
from app.database import sync_engine
from app.models import Stock
# Seed script will be implemented in Phase 2
print('Stock seeding not yet implemented - will be added in Phase 2A')
"

echo "Done!"
