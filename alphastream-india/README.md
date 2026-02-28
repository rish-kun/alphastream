# AlphaStream India - Financial News Analyzer

A comprehensive financial news analysis platform focused on Indian markets, providing real-time sentiment analysis, LLM-powered insights, and market intelligence.

## Architecture

```
alphastream-india/
├── backend/           # FastAPI Application
├── pipelines/         # Data Processing Pipelines (Celery)
└── frontend/          # Next.js Application
```

## Prerequisites

- Python 3.11+
- Node.js 18+
- Bun (for frontend)
- Docker & Docker Compose
- PostgreSQL 16
- Redis 7

## Quick Start

### 1. Start Infrastructure Services

```bash
docker-compose up -d
```

This will start PostgreSQL and Redis services.

### 2. Backend Setup

```bash
cd backend

# Create virtual environment and install dependencies
uv sync

# Copy environment variables
cp .env.example .env

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload
```

### 3. Pipelines Setup

```bash
cd pipelines

# Create virtual environment and install dependencies
uv sync

# Copy environment variables
cp .env.example .env

# Start Celery worker
celery -A tasks worker --loglevel=info

# Start Celery beat (in another terminal)
celery -A tasks beat --loglevel=info
```

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
bun install

# Copy environment variables
cp .env.example .env.local

# Start development server
bun dev
```

## Environment Variables

### Backend (.env)
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `SECRET_KEY` - JWT secret key
- `GEMINI_API_KEY` - Google Gemini API key
- `OPENROUTER_API_KEY` - OpenRouter API key

### Pipelines (.env)
- Same as backend plus:
- `CELERY_BROKER_URL` - Celery broker URL

### Frontend (.env.local)
- `NEXT_PUBLIC_API_URL` - Backend API URL
- `NEXT_PUBLIC_WS_URL` - WebSocket URL

## Features

- **Real-time News Scraping**: Automated scraping from major Indian financial news sources
- **Sentiment Analysis**: ML-powered sentiment analysis using transformer models
- **LLM Analysis**: Advanced market insights using Gemini and OpenRouter
- **Live Updates**: WebSocket-based real-time data streaming
- **Market Dashboard**: Interactive charts and visualizations

## Development

### Backend Development

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### Frontend Development

```bash
cd frontend
bun dev
```

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
bun test
```

## API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## License

MIT
