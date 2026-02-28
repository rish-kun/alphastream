"""Extensive research API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.services.research_service import ResearchService

router = APIRouter(prefix="/research", tags=["research"])


# ─── Request/Response schemas ────────────────────────────────────────────


class ResearchTaskResponse(BaseModel):
    task_id: str
    status: str
    message: str


class TopicResearchRequest(BaseModel):
    topic: str = Field(
        ..., min_length=2, max_length=200, description="Topic or query to research"
    )


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    progress: dict | None = None
    result: dict | None = None
    error: str | None = None


# ─── Endpoints ───────────────────────────────────────────────────────────


@router.post("/stock/{ticker}", response_model=ResearchTaskResponse, status_code=202)
async def research_stock(
    ticker: str,
    current_user: User = Depends(get_current_user),
):
    """Trigger extensive research for a specific stock.

    Uses Firecrawl, Browse.ai, and Thunderbit to perform deep web research
    on the given stock ticker. Results are processed through the ML pipeline
    and available via WebSocket updates.
    """
    task_id = ResearchService.research_stock(
        ticker=ticker.upper(),
        user_id=str(current_user.id),
    )
    return ResearchTaskResponse(
        task_id=task_id,
        status="dispatched",
        message=f"Extensive research started for {ticker.upper()}",
    )


@router.post(
    "/portfolio/{portfolio_id}", response_model=ResearchTaskResponse, status_code=202
)
async def research_portfolio(
    portfolio_id: str,
    current_user: User = Depends(get_current_user),
):
    """Trigger extensive research for all stocks in a portfolio."""
    task_id = ResearchService.research_portfolio(
        portfolio_id=portfolio_id,
        user_id=str(current_user.id),
    )
    return ResearchTaskResponse(
        task_id=task_id,
        status="dispatched",
        message=f"Extensive research started for portfolio",
    )


@router.post("/topic", response_model=ResearchTaskResponse, status_code=202)
async def research_topic(
    body: TopicResearchRequest,
    current_user: User = Depends(get_current_user),
):
    """Trigger extensive research for a freeform topic/query."""
    task_id = ResearchService.research_topic(
        topic=body.topic,
        user_id=str(current_user.id),
    )
    return ResearchTaskResponse(
        task_id=task_id,
        status="dispatched",
        message=f"Extensive research started for topic: {body.topic}",
    )


@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_research_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
):
    """Check the status of an extensive research task."""
    return ResearchService.get_task_status(task_id)
