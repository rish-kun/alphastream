# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

AlphaStream India is a financial news sentiment analysis platform for the Indian stock market. It aggregates news from RSS, Reddit, Twitter, and web scraping; processes it through FinBERT + spaCy NER + LLM pipelines; computes alpha signals; and streams results to a Next.js dashboard via WebSockets.

## Commands

### Backend (FastAPI)
```bash
cd backend
uv sync                                          # install dependencies
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
uv run pytest app/tests/ -v                      # all tests
uv run pytest app/tests/test_auth.py -v          # single test file
uv run alembic upgrade head                      # run migrations
uv run alembic revision --autogenerate -m "desc" # new migration
uv run python scripts/seed_stocks.py            # seed Nifty 50 stocks
```

### Pipeline (Celery)
```bash
cd pipeline
uv sync                     # without ML models
uv sync --extra ml          # with FinBERT/PyTorch (~2 GB)
uv run python -m spacy download en_core_web_sm
uv run celery -A pipeline.celery_app worker --loglevel=info
uv run celery -A pipeline.celery_app beat --loglevel=info
# Multi-queue worker (high priority first):
uv run celery -A pipeline.celery_app worker -Q high_priority,sentiment,google_news,celery -l info
uv run pytest tests/ -v
uv run pytest tests/test_scrapers.py -v
```

### Frontend (Next.js)
```bash
cd frontend
bun install
bun run dev
bun run build
bun run test:run                                 # all tests (Vitest)
bun run vitest run src/__tests__/lib/api.test.ts # single test file
```

### Infrastructure
```bash
docker compose up -d                             # start Postgres (5433) + Redis (6380)
docker compose down
docker compose down -v                           # also deletes data volumes
./scripts/start-local.sh                         # start all 4 app services
./scripts/stop-local.sh
```

## Architecture

Four services communicate at runtime:

```
Frontend (Next.js :3000)
    --> REST + WebSocket --> Backend (FastAPI :8000)
                                 |
                           PostgreSQL :5433
                           Redis :6380 (Celery broker + WS pub/sub)
                                 |
                    Pipeline (Celery Worker + Beat)
```

**Ports use non-standard offsets** to avoid conflicts: PostgreSQL is on 5433, Redis on 6380.

### Backend (`backend/app/`)
- `main.py` — FastAPI app, CORS, lifespan hooks
- `config.py` — all settings loaded from `.env` via pydantic-settings
- `database.py` — async SQLAlchemy engine (asyncpg driver)
- `api/v1/` — route handlers: `auth`, `stocks`, `news`, `portfolio`, `sentiment`, `websocket`, `research`
- `models/` — SQLAlchemy ORM models (User, Stock, NewsArticle, Sentiment, Portfolio, etc.)
- `schemas/` — Pydantic v2 request/response models
- `services/` — business logic, including `websocket_manager.py` for WS pub/sub via Redis
- `core/` — JWT security, OAuth helpers, exception handlers
- `tests/` — 81 pytest tests using pytest-asyncio

Migrations live in `alembic/versions/`. The single initial migration (`001_initial_schema.py`) creates all 9 tables.

### Pipeline (`pipeline/pipeline/`)
- `celery_app.py` — Celery config, beat schedules, task routing to queues (`high_priority`, `sentiment`, `google_news`, `celery`)
- `config.py` — pipeline-specific settings
- `database.py` — **sync** SQLAlchemy (Celery tasks are synchronous)
- `scrapers/` — RSS (feedparser), full-text (newspaper4k), Reddit (PRAW), Twitter, Google News, Firecrawl, Browse.ai, Thunderbit
- `ml/` — FinBERT sentiment classifier, spaCy NER, embeddings, ticker resolver (entity -> NSE ticker)
- `llm/` — Gemini and OpenRouter clients with key rotation and rate limiting
- `alpha/` — composite signal, expectation gap, narrative velocity, sentiment-price divergence
- `tasks/` — Celery task definitions; each maps roughly to a pipeline stage

Beat schedule overview: RSS (10 min) → web scrape (15 min) → Reddit/Twitter (30 min) → Google News (20 min) → sentiment (5 min) → alpha (15 min).

### Frontend (`frontend/src/`)
- Uses Next.js 15 App Router with TypeScript
- `lib/api.ts` — central fetch wrapper; reads `NEXT_PUBLIC_API_URL`
- `lib/ws.ts` — WebSocket client; reads `NEXT_PUBLIC_WS_URL`
- `lib/auth.ts` — JWT token handling (access + refresh)
- `providers/` — React context providers (auth state, query client)
- `hooks/` — custom React hooks wrapping TanStack Query calls
- `components/ui/` — shadcn/ui primitives (do not edit manually; use `bunx shadcn add`)
- State: Zustand for client state, TanStack Query for server state

## Key Design Decisions

- **Backend uses async SQLAlchemy** (`asyncpg`); pipeline uses **sync SQLAlchemy** because Celery workers are synchronous. Do not mix them.
- **WebSocket real-time delivery**: Backend subscribes to Redis pub/sub channels and pushes to connected clients; pipeline tasks publish to Redis after processing.
- **LLM key rotation**: Both `gemini_client.py` and `openrouter_client.py` accept comma-separated key lists in env vars (`GEMINI_API_KEYS`, `OPENROUTER_API_KEYS`) and rotate on rate-limit errors.
- **ML models are optional**: Pipeline has an `--extra ml` uv group for PyTorch/FinBERT. Without it, sentiment falls back to LLM-only analysis.
- **Extensive Research** is an on-demand Celery task (`pipeline.tasks.extensive_research`) triggered via `POST /api/v1/research/stock/{ticker}`; results are polled via `GET /api/v1/research/status/{task_id}`.

## Environment Setup

Copy `.env.example` to `.env`. Minimum required:
- `DATABASE_URL` — use port 5433 with Docker Compose
- `REDIS_URL` — use port 6380 with Docker Compose
- `SECRET_KEY` — JWT signing secret
- `GEMINI_API_KEYS` — required for LLM analysis

Frontend env vars (`NEXT_PUBLIC_*`) must be set at build time (not runtime) for Next.js.
