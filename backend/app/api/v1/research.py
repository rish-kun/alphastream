"""Extensive research API endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.database import get_db
from app.models.news import NewsArticle
from app.schemas.news import NewsArticleResponse
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


class ResearchSentimentSummary(BaseModel):
    overall_score: float | None
    overall_label: str
    analyzed_articles: int
    pending_articles: int
    bullish_count: int
    neutral_count: int
    bearish_count: int


class ResearchResultResponse(BaseModel):
    task_id: str
    status: str
    topic: str | None = None
    ticker: str | None = None
    new_articles: int
    total_found: int
    query_count: int | None = None
    started_at: str | None = None
    completed_at: str | None = None
    duration_seconds: float | None = None
    sentiment: ResearchSentimentSummary
    articles: list[NewsArticleResponse]


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


@router.get("/result/{task_id}", response_model=ResearchResultResponse)
async def get_research_result(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = ResearchService.get_task_result(task_id)
    task_status = task["status"]
    task_result = task["result"] or {}

    if task_status in {"PENDING", "PROGRESS"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Research is still in progress",
        )

    if task_status == "FAILURE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Research task failed",
        )

    if task_status != "SUCCESS" or not task_result:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Research result is unavailable",
        )

    owner_user_id = task_result.get("user_id")
    if owner_user_id and owner_user_id != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this research result",
        )

    article_ids_raw = task_result.get("article_ids")
    if not isinstance(article_ids_raw, list):
        article_ids_raw = []

    parsed_ids: list[uuid.UUID] = []
    for article_id in article_ids_raw:
        if not isinstance(article_id, str):
            continue
        try:
            parsed_ids.append(uuid.UUID(article_id))
        except ValueError:
            continue

    if parsed_ids:
        stmt = (
            select(NewsArticle)
            .where(NewsArticle.id.in_(parsed_ids))
            .options(selectinload(NewsArticle.sentiment_analyses))
            .order_by(NewsArticle.published_at.desc())
        )
        rows = await db.execute(stmt)
        articles_orm = rows.scalars().all()
    else:
        articles_orm = []

    articles = [NewsArticleResponse.model_validate(article) for article in articles_orm]
    scores: list[float] = []
    bullish = 0
    neutral = 0
    bearish = 0

    for article in articles:
        if not article.sentiment_analyses:
            continue
        score = float(article.sentiment_analyses[0].sentiment_score)
        scores.append(score)
        if score > 0.2:
            bullish += 1
        elif score < -0.2:
            bearish += 1
        else:
            neutral += 1

    overall_score = (sum(scores) / len(scores)) if scores else None
    if overall_score is None:
        overall_label = "unknown"
    elif overall_score > 0.2:
        overall_label = "bullish"
    elif overall_score < -0.2:
        overall_label = "bearish"
    else:
        overall_label = "neutral"

    sentiment = ResearchSentimentSummary(
        overall_score=overall_score,
        overall_label=overall_label,
        analyzed_articles=len(scores),
        pending_articles=max(0, len(articles) - len(scores)),
        bullish_count=bullish,
        neutral_count=neutral,
        bearish_count=bearish,
    )

    return ResearchResultResponse(
        task_id=task_id,
        status=task_status,
        topic=task_result.get("topic"),
        ticker=task_result.get("ticker"),
        new_articles=int(task_result.get("new_articles", 0)),
        total_found=int(task_result.get("total_found", 0)),
        query_count=task_result.get("query_count"),
        started_at=task_result.get("started_at"),
        completed_at=task_result.get("completed_at"),
        duration_seconds=task_result.get("duration_seconds"),
        sentiment=sentiment,
        articles=articles,
    )
