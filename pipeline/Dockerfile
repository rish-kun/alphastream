FROM python:3.12-slim AS base

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies (without optional ML extras by default)
RUN uv sync --frozen --no-dev

# Download spaCy model
RUN uv run python -m spacy download en_core_web_sm

# Copy application code
COPY pipeline/ ./pipeline/

# Default command: Celery worker
# Override in docker-compose for beat scheduler
CMD ["uv", "run", "celery", "-A", "pipeline.celery_app", "worker", "--loglevel=info"]
