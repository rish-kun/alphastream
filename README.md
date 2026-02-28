# AlphaStream India

Institutional-grade financial news sentiment analysis platform for the Indian stock market.

AlphaStream aggregates news from multiple sources (RSS feeds, web scraping, Reddit, Twitter), processes it through ML and LLM pipelines (FinBERT, spaCy NER, Gemini, OpenRouter), computes alpha-generation metrics, and streams actionable insights to users in real time via WebSockets.

---

## Table of Contents

- [Features](#features)
- [Architecture Overview](#architecture-overview)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Docker (Full Stack)](#docker-full-stack)
- [Manual Setup (Step by Step)](#manual-setup-step-by-step)
- [Configuration (.env)](#configuration-env)
- [Running the Application](#running-the-application)
- [Stopping the Application](#stopping-the-application)
- [Database Setup](#database-setup)
- [Running Tests](#running-tests)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Extensive Research Feature](#extensive-research-feature)
- [Troubleshooting](#troubleshooting)

---

## Features

- **Real-time News Aggregation** -- RSS feeds, web scraping, Reddit, and Twitter sources focused on Indian markets
- **ML-Powered Sentiment Analysis** -- FinBERT for financial sentiment classification, spaCy NER for entity extraction
- **LLM Integration** -- Gemini and OpenRouter for advanced analysis summaries and market narrative generation
- **Alpha Metrics** -- Expectation Gap, Narrative Velocity, Sentiment-Price Divergence signals
- **Live Dashboard** -- Real-time WebSocket updates, sector heatmaps, sentiment charts
- **Portfolio Tracking** -- Create watchlists, track portfolio sentiment exposure
- **Extensive Research Mode** -- On-demand deep research using Firecrawl, Browse.ai, and Thunderbit for comprehensive coverage
- **Nifty 50 Coverage** -- Pre-loaded with all 50 Nifty index constituents
- **JWT Authentication** -- Secure user accounts with registration and login

---

## Architecture Overview

The platform consists of four services that run together:

```
Frontend (Next.js)  -->  Backend (FastAPI)  -->  PostgreSQL
    :3000                   :8000                  :5433
                                |
                            WebSockets
                                |
                          Redis  :6380
                                |
                    Pipeline (Celery Worker + Beat)
                        - RSS ingestion
                        - Web scraping
                        - Reddit/Twitter scrapers
                        - FinBERT sentiment analysis
                        - spaCy NER
                        - LLM analysis (Gemini/OpenRouter)
                        - Alpha metric computation
                        - Extensive research (Firecrawl/Browse.ai/Thunderbit)
```

| Service | Port | Description |
|---------|------|-------------|
| Frontend | 3000 | Next.js 15 dashboard UI |
| Backend | 8000 | FastAPI REST API + WebSocket server |
| PostgreSQL | 5433 | Primary database (mapped from container port 5432) |
| Redis | 6380 | Celery broker + WebSocket pub/sub (mapped from 6379) |

> Ports 5433 and 6380 are used to avoid conflicts with any PostgreSQL/Redis instances you may already have running.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15, React 19, TypeScript, Tailwind CSS v4, shadcn/ui, TanStack Query, Zustand, Recharts |
| Backend | FastAPI, SQLAlchemy 2.0 (async), PyJWT, bcrypt, Alembic |
| Pipeline | Celery + Redis, FinBERT (transformers), spaCy, newspaper4k, feedparser, PRAW, yfinance |
| LLM | Google Gemini (google-genai), OpenRouter (openai SDK) |
| Database | PostgreSQL 16, Redis 7 |
| Package Managers | uv (Python), Bun (JavaScript) |
| Testing | pytest (backend + pipeline), Vitest (frontend) |
| CI/CD | GitHub Actions (4 parallel jobs) |

---

## Prerequisites

You need the following installed on your machine before starting. If you do not have them, follow the installation links.

### 1. Python 3.12+

Check: `python3 --version`

Install: https://www.python.org/downloads/ (choose 3.12 or newer)

### 2. uv (Python package manager)

Check: `uv --version`

Install:
```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 3. Node.js 18+

Check: `node --version`

Install: https://nodejs.org/ (LTS version recommended)

### 4. Bun (JavaScript package manager)

Check: `bun --version`

Install:
```bash
# macOS / Linux
curl -fsSL https://bun.sh/install | bash

# Windows
powershell -c "irm bun.sh/install.ps1 | iex"
```

### 5. Docker and Docker Compose

Required only for running PostgreSQL and Redis. If you already have PostgreSQL 16 and Redis 7 running locally, you can skip Docker and just update the connection URLs in `.env`.

Check: `docker --version && docker compose version`

Install: https://docs.docker.com/get-docker/

### 6. Git

Check: `git --version`

Install: https://git-scm.com/downloads

---

## Quick Start

If you want to get up and running as fast as possible:

```bash
# 1. Clone the repository
git clone <repository-url>
cd as2

# 2. Run the automated setup script
chmod +x scripts/*.sh
./scripts/setup.sh

# 3. Edit the .env file with your API keys (see Configuration section below)
#    At minimum, you need GEMINI_API_KEYS for LLM features to work.

# 4. Start PostgreSQL and Redis (or skip this and use Docker for everything —
#    see the "Docker (Full Stack)" section below)
docker compose up -d

# 5. Run database migrations and seed stock data
cd backend
uv run alembic upgrade head
uv run python scripts/seed_stocks.py
cd ..

# 6. Start all services
./scripts/start-local.sh
```

After a minute or so, open your browser:
- **Dashboard**: http://localhost:3000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/v1/health

To stop everything:
```bash
./scripts/stop-local.sh
```

If you want to run everything in Docker instead, see the [Docker (Full Stack)](#docker-full-stack) section.

---

## Docker (Full Stack)

You can run **all** services -- frontend, backend, pipeline (Celery worker + beat), PostgreSQL, and Redis -- in Docker with a single command. No need to install Python, Node.js, uv, or Bun on your host machine. The only prerequisite is Docker.

### Production Mode

```bash
# 1. Copy and configure .env
cp .env.example .env
# Edit .env with your API keys (see Configuration section below)

# 2. Start the full stack
docker compose up --build -d

# That's it! All 6 services start automatically:
#   - PostgreSQL + Redis          (infrastructure)
#   - Backend                     (runs migrations + seeds data on startup)
#   - Celery worker + beat        (pipeline)
#   - Frontend                    (production build)
```

Once everything is up, open your browser:

| Service | URL |
|---------|-----|
| Dashboard | http://localhost:3000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| API Docs (ReDoc) | http://localhost:8000/redoc |
| Health Check | http://localhost:8000/api/v1/health |

### Development Mode (Live Code Reloading)

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

The development override file (`docker-compose.dev.yml`) makes the following changes:

- **Backend** -- mounts `./backend` into the container and runs uvicorn with `--reload`, so code changes take effect immediately.
- **Worker / Beat** -- mounts `./pipeline` into the containers so task code changes are picked up on the next execution.
- **Frontend** -- mounts `./frontend/src` and `./frontend/public` into the container and runs `bun run dev` instead of the production build, giving you full hot-reload.

### Useful Docker Commands

```bash
# Tail logs for a specific service
docker compose logs -f alphastream-backend
docker compose logs -f alphastream-worker

# Check service status
docker compose ps

# Stop everything
docker compose down

# Stop and delete all data volumes (removes database data)
docker compose down -v

# Rebuild and restart only the backend
docker compose up --build alphastream-backend
```

### Docker vs Local Development

| | Docker | Local |
|---|---|---|
| Prerequisites | Docker only | Python 3.12, uv, Node.js, Bun |
| Setup time | ~2 minutes | ~10 minutes |
| Code hot-reload | Dev mode only | Always |
| Port mapping | Same ports | Same ports |
| Recommended for | Quick start, testing | Active development |

### Port Mapping Note

PostgreSQL is exposed on port **5433** (not 5432) and Redis on port **6380** (not 6379) to avoid conflicts with any local PostgreSQL or Redis instances you may already have running. Inside the Docker network, services communicate on the standard ports (5432 and 6379).

---

## Manual Setup (Step by Step)

If the quick start does not work or you prefer to understand each step, follow this section.

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd as2
```

### Step 2: Create the Environment File

```bash
cp .env.example .env
```

Open `.env` in a text editor and fill in your API keys. See [Configuration](#configuration-env) for details on each variable.

### Step 3: Install Backend Dependencies

```bash
cd backend
uv sync
cd ..
```

### Step 4: Install Pipeline Dependencies

```bash
cd pipeline
uv sync
cd ..
```

To also install ML model dependencies (FinBERT -- requires ~2 GB disk space for PyTorch):
```bash
cd pipeline
uv sync --extra ml
cd ..
```

### Step 5: Download the spaCy Language Model

```bash
cd pipeline
uv run python -m spacy download en_core_web_sm
cd ..
```

### Step 6: Install Frontend Dependencies

```bash
cd frontend
bun install
cd ..
```

### Step 7: Start PostgreSQL and Redis

**Option A: Using Docker Compose (recommended)**

```bash
docker compose up -d
```

This starts:
- PostgreSQL 16 on port **5433** (container maps 5432 -> 5433)
- Redis 7 on port **6380** (container maps 6379 -> 6380)

Verify they are running:
```bash
docker compose ps
```

**Option B: Using existing local installations**

If you already have PostgreSQL and Redis running, update the connection strings in your `.env`:

```env
DATABASE_URL=postgresql+asyncpg://your_user:your_password@localhost:5432/alphastream
REDIS_URL=redis://localhost:6379/0
```

Make sure to create the `alphastream` database:
```bash
createdb alphastream
```

### Step 8: Run Database Migrations

```bash
cd backend
uv run alembic upgrade head
cd ..
```

This creates all 9 database tables (users, stocks, articles, sentiments, portfolios, etc.).

### Step 9: Seed Stock Data

```bash
cd backend
uv run python scripts/seed_stocks.py
cd ..
```

This inserts all 50 Nifty index constituents into the stocks table.

### Step 10: Start All Services

You can either start all 4 services at once or individually.

**All at once:**
```bash
./scripts/start-local.sh
```

**Individually (in separate terminal windows):**

Terminal 1 -- Backend:
```bash
cd backend
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Terminal 2 -- Celery Worker:
```bash
cd pipeline
uv run celery -A pipeline.celery_app worker --loglevel=info
```

Terminal 3 -- Celery Beat (scheduler):
```bash
cd pipeline
uv run celery -A pipeline.celery_app beat --loglevel=info
```

Terminal 4 -- Frontend:
```bash
cd frontend
bun run dev
```

---

## Configuration (.env)

Below is every environment variable with an explanation. Only a few are strictly required to start the app; the rest enable additional features.

### Required

| Variable | Example | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5433/alphastream` | PostgreSQL connection string. Use port 5433 if using the Docker Compose setup. |
| `REDIS_URL` | `redis://localhost:6380/0` | Redis connection string. Use port 6380 if using Docker Compose. |
| `SECRET_KEY` | `change-me-to-a-random-secret-in-production` | Secret key for signing JWT tokens. Change this in production. |

### Backend / Auth

| Variable | Default | Description |
|----------|---------|-------------|
| `ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | How long access tokens are valid |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | How long refresh tokens are valid |
| `GOOGLE_CLIENT_ID` | _(empty)_ | Google OAuth client ID (optional, not yet active) |
| `GOOGLE_CLIENT_SECRET` | _(empty)_ | Google OAuth client secret (optional, not yet active) |
| `GITHUB_CLIENT_ID` | _(empty)_ | GitHub OAuth client ID (optional, not yet active) |
| `GITHUB_CLIENT_SECRET` | _(empty)_ | GitHub OAuth client secret (optional, not yet active) |

### AI / LLM APIs

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEYS` | Comma-separated list of Google Gemini API keys (supports key rotation). Get a key at https://aistudio.google.com/apikey |
| `OPENROUTER_API_KEYS` | Comma-separated list of OpenRouter API keys. Get a key at https://openrouter.ai/keys |

### Reddit API

| Variable | Description |
|----------|-------------|
| `REDDIT_CLIENT_ID` | Reddit app client ID. Create an app at https://www.reddit.com/prefs/apps |
| `REDDIT_CLIENT_SECRET` | Reddit app client secret |
| `REDDIT_USER_AGENT` | User agent string (default: `AlphaStream/0.1`) |

### Frontend

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000/api/v1` | Backend API URL (used by the frontend) |
| `NEXT_PUBLIC_WS_URL` | `ws://localhost:8000/api/v1` | WebSocket URL (used by the frontend) |

### Pipeline

| Variable | Default | Description |
|----------|---------|-------------|
| `FINBERT_MODEL` | `ProsusAI/finbert` | HuggingFace model ID for sentiment analysis |
| `SPACY_MODEL` | `en_core_web_sm` | spaCy model for named entity recognition |
| `LLM_REQUESTS_PER_MINUTE` | `15` | Rate limit for LLM API calls |
| `SCRAPE_TIMEOUT` | `30` | Timeout in seconds for web scraping requests |
| `MAX_ARTICLES_PER_FEED` | `50` | Maximum articles to process per RSS feed |

### Extensive Research APIs (Optional)

These enable the "Extensive Research" toggle on stock, portfolio, and news pages. The feature works without them but will skip the corresponding service.

| Variable | Description |
|----------|-------------|
| `FIRECRAWL_API_KEY` | Firecrawl API key. Get one at https://www.firecrawl.dev/ |
| `BROWSEAI_API_KEY` | Browse.ai API key. Get one at https://www.browse.ai/ |
| `BROWSEAI_DEFAULT_ROBOT_ID` | Browse.ai robot ID for your configured scraping robot |
| `THUNDERBIT_API_KEY` | Thunderbit API key. Get one at https://thunderbit.com/ |

---

## Running the Application

### Start Everything

```bash
# Make sure PostgreSQL and Redis are running first
docker compose up -d

# Start all 4 services (backend, celery worker, celery beat, frontend)
./scripts/start-local.sh
```

### Access Points

| Service | URL |
|---------|-----|
| Dashboard | http://localhost:3000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| API Docs (ReDoc) | http://localhost:8000/redoc |
| Health Check | http://localhost:8000/api/v1/health |

---

## Stopping the Application

```bash
# Stop all 4 application services
./scripts/stop-local.sh

# Stop PostgreSQL and Redis containers
docker compose down

# To also delete database volumes (removes all data):
docker compose down -v
```

---

## Database Setup

### Run Migrations

```bash
cd backend
uv run alembic upgrade head
```

### Seed Nifty 50 Stocks

```bash
cd backend
uv run python scripts/seed_stocks.py
```

### Create a New Migration

If you modify the SQLAlchemy models:
```bash
cd backend
uv run alembic revision --autogenerate -m "description of change"
uv run alembic upgrade head
```

### Reset the Database

```bash
cd backend
uv run alembic downgrade base
uv run alembic upgrade head
uv run python scripts/seed_stocks.py
```

---

## Running Tests

### All Tests

```bash
# Backend (81 tests)
cd backend && uv run pytest app/tests/ -v && cd ..

# Pipeline (111 tests)
cd pipeline && uv run pytest tests/ -v && cd ..

# Frontend (22 tests)
cd frontend && bun run test:run && cd ..
```

### Individual Test Files

```bash
# Backend example
cd backend
uv run pytest app/tests/test_auth.py -v

# Pipeline example
cd pipeline
uv run pytest tests/test_scrapers.py -v

# Frontend example
cd frontend
bun run vitest run src/__tests__/lib/api.test.ts
```

### Test Summary

| Component | Tests | Framework |
|-----------|-------|-----------|
| Backend | 81 | pytest + pytest-asyncio |
| Pipeline | 111 | pytest |
| Frontend | 22 | Vitest + Testing Library |
| **Total** | **214** | |

---

## Project Structure

```
as2/
├── .env.example                  # Environment variable template
├── .github/workflows/ci.yml     # CI pipeline (4 parallel jobs)
├── docker-compose.yml            # Full stack (all 6 services)
├── docker-compose.dev.yml        # Dev overrides
├── scripts/
│   ├── setup.sh                  # First-time setup (installs everything)
│   ├── start-local.sh            # Starts all 4 services
│   ├── stop-local.sh             # Stops all services
│   └── seed-data.sh              # Runs migrations
│
├── backend/                      # FastAPI Backend
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/                  # Database migrations
│   │   └── versions/
│   │       └── 001_initial_schema.py
│   ├── scripts/
│   │   └── seed_stocks.py        # Nifty 50 stock seeder
│   └── app/
│       ├── main.py               # FastAPI application entry point
│       ├── config.py             # Settings (reads .env)
│       ├── database.py           # Async SQLAlchemy engine
│       ├── api/v1/               # API route handlers
│       │   ├── router.py         # Aggregates all routers
│       │   ├── auth.py           # Registration, login, token refresh
│       │   ├── stocks.py         # Stock lookup, search, prices
│       │   ├── news.py           # News articles, filtering
│       │   ├── portfolio.py      # Portfolio CRUD, watchlists
│       │   ├── sentiment.py      # Sentiment aggregation
│       │   ├── websocket.py      # WebSocket endpoints
│       │   └── research.py       # Extensive research triggers
│       ├── models/               # SQLAlchemy ORM models (9 tables)
│       ├── schemas/              # Pydantic v2 request/response schemas
│       ├── services/             # Business logic layer
│       ├── core/                 # Security, OAuth, exceptions
│       └── tests/                # 81 unit tests
│
├── pipeline/                     # Data Pipeline & ML
│   ├── pyproject.toml            # Dependencies (ML models are optional)
│   └── pipeline/
│       ├── celery_app.py         # Celery configuration + beat schedules
│       ├── config.py             # Pipeline settings
│       ├── database.py           # Sync SQLAlchemy (for Celery tasks)
│       ├── scrapers/             # Data collection
│       │   ├── rss_feeds.py      # Indian financial RSS sources
│       │   ├── article_scraper.py # newspaper4k-based scraper
│       │   ├── reddit_client.py  # PRAW Reddit scraper
│       │   ├── twitter_client.py # Twitter scraper
│       │   ├── firecrawl_client.py    # Firecrawl integration
│       │   ├── browseai_client.py     # Browse.ai integration
│       │   └── thunderbit_client.py   # Thunderbit integration
│       ├── ml/                   # Machine learning
│       │   ├── finbert.py        # FinBERT sentiment classifier
│       │   ├── ner.py            # spaCy named entity recognition
│       │   ├── embeddings.py     # Text embeddings
│       │   └── ticker_resolver.py # Maps entities to stock tickers
│       ├── llm/                  # LLM integrations
│       │   ├── gemini_client.py  # Google Gemini
│       │   ├── openrouter_client.py # OpenRouter (multiple models)
│       │   ├── prompts.py        # Prompt templates
│       │   └── rate_limiter.py   # API rate limiting
│       ├── alpha/                # Alpha signal computation
│       │   ├── composite_signal.py    # Combined alpha score
│       │   ├── expectation_gap.py     # Consensus vs. sentiment gap
│       │   ├── narrative_velocity.py  # News momentum tracking
│       │   └── divergence.py          # Sentiment-price divergence
│       ├── tasks/                # Celery task definitions
│       │   ├── rss_ingestion.py
│       │   ├── web_scraper.py
│       │   ├── reddit_scraper.py
│       │   ├── twitter_scraper.py
│       │   ├── sentiment_analysis.py
│       │   ├── ticker_identification.py
│       │   ├── alpha_metrics.py
│       │   └── extensive_research.py  # On-demand deep research
│       └── utils/                # Shared utilities
│
├── frontend/                     # Next.js Frontend
│   ├── package.json
│   ├── vitest.config.ts
│   ├── components.json           # shadcn/ui config
│   └── src/
│       ├── app/                  # Next.js App Router pages
│       │   ├── globals.css       # Tailwind v4 theme
│       │   ├── layout.tsx        # Root layout with providers
│       │   ├── (auth)/           # Login + Register pages
│       │   ├── dashboard/        # Main dashboard
│       │   ├── stocks/           # Stock search + detail pages
│       │   ├── news/             # News feed + article detail
│       │   └── portfolio/        # Portfolio management
│       ├── components/
│       │   ├── ui/               # 22+ shadcn/ui components
│       │   ├── layout/           # Navbar, Sidebar
│       │   ├── dashboard/        # Live feed, charts, metrics
│       │   ├── stocks/           # Stock cards, search, detail
│       │   ├── news/             # News cards, sentiment badge
│       │   ├── portfolio/        # Portfolio manager, watchlist
│       │   └── research/         # Research toggle component
│       ├── lib/                  # API client, WebSocket, auth
│       ├── providers/            # React context providers
│       ├── hooks/                # Custom React hooks
│       ├── types/                # TypeScript type definitions
│       └── __tests__/            # 22 frontend tests
```

---

## API Documentation

Once the backend is running, interactive API documentation is available at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/register` | Create a new account |
| `POST` | `/api/v1/auth/login` | Log in and get JWT tokens |
| `POST` | `/api/v1/auth/refresh` | Refresh an expired access token |
| `GET` | `/api/v1/stocks/` | List stocks (with search, sector filter) |
| `GET` | `/api/v1/stocks/{ticker}` | Get stock details + latest price |
| `GET` | `/api/v1/news/` | List news articles (with filters) |
| `GET` | `/api/v1/news/{id}` | Get article detail with sentiment |
| `GET` | `/api/v1/portfolio/` | List user portfolios |
| `POST` | `/api/v1/portfolio/` | Create a new portfolio |
| `GET` | `/api/v1/sentiment/aggregate` | Aggregated sentiment data |
| `WS` | `/api/v1/ws/news` | Real-time news stream |
| `WS` | `/api/v1/ws/sentiment` | Real-time sentiment updates |
| `POST` | `/api/v1/research/stock/{ticker}` | Trigger extensive research for a stock |
| `POST` | `/api/v1/research/portfolio/{id}` | Trigger research for portfolio stocks |
| `POST` | `/api/v1/research/topic` | Research a custom topic |
| `GET` | `/api/v1/research/status/{task_id}` | Check research task progress |

---

## Extensive Research Feature

The platform includes an optional deep research mode that uses three external services for more comprehensive news and data collection. This feature is activated via a toggle on stock detail, portfolio, and news pages.

**How it works:**
1. User enables the "Extensive Research" toggle on a stock/portfolio/news page
2. The frontend sends a request to the research API endpoint
3. The backend dispatches a Celery task that orchestrates:
   - **Firecrawl** -- Searches and scrapes relevant web pages
   - **Browse.ai** -- Uses pre-trained robots for structured data extraction
   - **Thunderbit** -- AI-powered scraping for additional sources
4. Results are processed through the same ML/LLM pipeline and stored in the database
5. The frontend polls for task completion and refreshes data

**Setup:** Add your API keys to `.env`. The feature degrades gracefully -- if a service key is missing, that service is simply skipped.

---

## Troubleshooting

### "Port already in use" errors

The application uses non-standard ports (5433, 6380) to avoid conflicts, but if you still see port errors:

```bash
# Check what is using a port
lsof -i :8000
lsof -i :3000

# Kill processes using the stop script
./scripts/stop-local.sh
```

### Docker containers not starting

```bash
# Check container status
docker compose ps

# View logs
docker compose logs alphastream-postgres
docker compose logs alphastream-redis

# Restart containers
docker compose down && docker compose up -d
```

### Database migration errors

```bash
# Check current migration state
cd backend
uv run alembic current

# Reset and re-run all migrations
uv run alembic downgrade base
uv run alembic upgrade head
```

### "Module not found" errors

Make sure you installed dependencies for the correct component:

```bash
# Backend
cd backend && uv sync

# Pipeline (without ML models)
cd pipeline && uv sync

# Pipeline (with ML models -- requires ~2 GB)
cd pipeline && uv sync --extra ml

# Frontend
cd frontend && bun install
```

### spaCy model not found

```bash
cd pipeline
uv run python -m spacy download en_core_web_sm
```

### Celery worker not connecting to Redis

Verify Redis is running and accessible:
```bash
redis-cli -p 6380 ping
# Should respond: PONG
```

Check that `REDIS_URL` in `.env` matches your Redis instance's port.

### Frontend not connecting to backend

Check that:
1. The backend is running on port 8000
2. `NEXT_PUBLIC_API_URL` in `.env` is set to `http://localhost:8000/api/v1`
3. CORS is not blocking requests (the backend allows all origins in development)

---

## License

This project is private and not licensed for public distribution.
