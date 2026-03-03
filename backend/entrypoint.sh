#!/usr/bin/env bash
set -e

echo "=== AlphaStream Backend Entrypoint ==="

# Run database migrations
echo "Running database migrations..."
uv run alembic upgrade head
echo "Migrations complete."

# Seed stock data (idempotent — uses ON CONFLICT DO NOTHING)
echo "Seeding stock data..."
uv run python scripts/seed_stocks.py
echo "Seed complete."

# Start the application
echo "Starting FastAPI server..."
exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
