from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.config import settings
from app.core.exceptions import register_exception_handlers

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown logic."""
    logger.info("AlphaStream India backend starting up...")
    yield
    logger.info("AlphaStream India backend shutting down...")
    from app.services.websocket_manager import manager

    await manager.cleanup()


app = FastAPI(
    title="AlphaStream India",
    description="Institutional-grade financial news sentiment analysis for Indian markets",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register custom exception handlers
register_exception_handlers(app)

# Include all API v1 routes
app.include_router(api_router)


@app.get("/api/v1/health", tags=["health"])
async def health_check() -> dict:
    return {
        "status": "healthy",
        "service": "alphastream-backend",
        "version": "0.1.0",
        "timestamp": datetime.now(UTC).isoformat(),
    }
