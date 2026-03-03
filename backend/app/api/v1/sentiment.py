from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

from celery import Celery
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.config import settings
from app.database import get_db
from app.models.news import ArticleStockMention, NewsArticle
from app.models.sentiment import AlphaMetric, SentimentAnalysis
from app.models.stock import Stock
from app.models.user import User
from app.schemas.sentiment import (
    AlphaMetricResponse,
    SectorSentiment,
    SentimentOverview,
)

router = APIRouter(prefix="/sentiment", tags=["sentiment"])

_celery_app = Celery(
    "alphastream-sentiment",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)


class SentimentReanalysisRequest(BaseModel):
    article_ids: list[uuid.UUID] = Field(..., min_length=1, max_length=100)
    force_reanalyze: bool = True


class SentimentReanalysisResponse(BaseModel):
    dispatched: int
    task_ids: list[str]
    skipped_article_ids: list[uuid.UUID]


@router.get("/overview", response_model=SentimentOverview)
async def get_market_sentiment(
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> SentimentOverview:
    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=24)

    # Get average sentiment from recent analyses (last 24h)
    avg_stmt = select(func.avg(SentimentAnalysis.sentiment_score)).where(
        SentimentAnalysis.analyzed_at >= since
    )
    avg_result = await db.execute(avg_stmt)
    market_sentiment = avg_result.scalar_one() or 0.0

    # Count bullish (score > 0.3), bearish (score < -0.3), neutral
    bullish_stmt = (
        select(func.count())
        .select_from(SentimentAnalysis)
        .where(
            and_(
                SentimentAnalysis.analyzed_at >= since,
                SentimentAnalysis.sentiment_score > 0.3,
            )
        )
    )
    bearish_stmt = (
        select(func.count())
        .select_from(SentimentAnalysis)
        .where(
            and_(
                SentimentAnalysis.analyzed_at >= since,
                SentimentAnalysis.sentiment_score < -0.3,
            )
        )
    )
    neutral_stmt = (
        select(func.count())
        .select_from(SentimentAnalysis)
        .where(
            and_(
                SentimentAnalysis.analyzed_at >= since,
                SentimentAnalysis.sentiment_score >= -0.3,
                SentimentAnalysis.sentiment_score <= 0.3,
            )
        )
    )

    bullish_result = await db.execute(bullish_stmt)
    bearish_result = await db.execute(bearish_stmt)
    neutral_result = await db.execute(neutral_stmt)

    bullish_count = bullish_result.scalar_one()
    bearish_count = bearish_result.scalar_one()
    neutral_count = neutral_result.scalar_one()

    # Get top movers by alpha composite_score (most recent metrics)
    top_movers_stmt = (
        select(AlphaMetric)
        .where(AlphaMetric.stock_id.isnot(None))
        .order_by(AlphaMetric.computed_at.desc(), AlphaMetric.composite_score.desc())
        .limit(10)
    )
    top_movers_result = await db.execute(top_movers_stmt)
    top_movers = top_movers_result.scalars().all()

    return SentimentOverview(
        market_sentiment=float(market_sentiment),
        bullish_count=bullish_count,
        bearish_count=bearish_count,
        neutral_count=neutral_count,
        top_movers=[AlphaMetricResponse.model_validate(m) for m in top_movers],
    )


@router.get("/top-signals", response_model=dict)
async def get_top_signals(
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> dict:
    # Pick the most recent metric per stock, then rank by composite score.
    ranked_metrics = (
        select(
            AlphaMetric.id.label("metric_id"),
            func.row_number()
            .over(
                partition_by=AlphaMetric.stock_id,
                order_by=(
                    AlphaMetric.computed_at.desc(),
                    AlphaMetric.window_hours.asc(),
                ),
            )
            .label("row_num"),
        )
        .where(AlphaMetric.stock_id.isnot(None))
        .subquery()
    )

    stmt = (
        select(
            Stock.ticker,
            Stock.company_name,
            AlphaMetric.composite_score,
            AlphaMetric.signal,
            AlphaMetric.conviction,
        )
        .join(ranked_metrics, ranked_metrics.c.metric_id == AlphaMetric.id)
        .join(Stock, Stock.id == AlphaMetric.stock_id)
        .where(ranked_metrics.c.row_num == 1)
        .order_by(AlphaMetric.composite_score.desc())
        .limit(limit)
    )

    result = await db.execute(stmt)
    rows = result.all()

    return {
        "signals": [
            {
                "ticker": row[0],
                "company_name": row[1],
                "composite_score": float(row[2]) if row[2] is not None else 0.0,
                "signal": row[3],
                "conviction": float(row[4]) if row[4] is not None else 0.0,
            }
            for row in rows
        ]
    }


@router.get("/sectors", response_model=list[SectorSentiment])
async def get_sector_sentiment(
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> list[SectorSentiment]:
    # Group by sector: avg sentiment, article count, top stocks per sector
    # Join SentimentAnalysis -> NewsArticle -> ArticleStockMention -> Stock
    # to get per-sector sentiment averages
    sector_stmt = (
        select(
            Stock.sector,
            func.avg(SentimentAnalysis.sentiment_score).label("avg_sentiment"),
            func.count(func.distinct(NewsArticle.id)).label("article_count"),
        )
        .select_from(SentimentAnalysis)
        .join(NewsArticle, SentimentAnalysis.article_id == NewsArticle.id)
        .join(ArticleStockMention, ArticleStockMention.article_id == NewsArticle.id)
        .join(Stock, Stock.id == ArticleStockMention.stock_id)
        .group_by(Stock.sector)
        .order_by(Stock.sector)
    )
    sector_result = await db.execute(sector_stmt)
    sector_rows = sector_result.all()

    results = []
    for row in sector_rows:
        sector = row[0]
        avg_sentiment = float(row[1]) if row[1] is not None else 0.0
        article_count = row[2]

        # Get top stocks for this sector (by alpha composite_score)
        top_stocks_stmt = (
            select(Stock.ticker)
            .join(AlphaMetric, AlphaMetric.stock_id == Stock.id)
            .where(Stock.sector == sector)
            .order_by(AlphaMetric.composite_score.desc())
            .limit(5)
        )
        top_stocks_result = await db.execute(top_stocks_stmt)
        top_stocks = [r[0] for r in top_stocks_result.all()]

        # Deduplicate tickers while preserving order
        seen = set()
        unique_stocks = []
        for t in top_stocks:
            if t not in seen:
                seen.add(t)
                unique_stocks.append(t)

        results.append(
            SectorSentiment(
                sector=sector,
                sentiment_score=avg_sentiment,
                article_count=article_count,
                top_stocks=unique_stocks,
            )
        )

    return results


@router.post("/reanalyze", response_model=SentimentReanalysisResponse, status_code=202)
async def reanalyze_articles_sentiment(
    body: SentimentReanalysisRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> SentimentReanalysisResponse:
    existing_rows = await db.execute(
        select(NewsArticle.id).where(NewsArticle.id.in_(body.article_ids))
    )
    existing_ids = {str(article_id) for article_id in existing_rows.scalars().all()}

    task_ids: list[str] = []
    skipped: list[uuid.UUID] = []

    for article_id in body.article_ids:
        article_id_str = str(article_id)
        if article_id_str not in existing_ids:
            skipped.append(article_id)
            continue

        task = _celery_app.send_task(
            "pipeline.tasks.sentiment_analysis.analyze_article",
            args=[article_id_str],
            kwargs={"force_reanalyze": body.force_reanalyze},
        )
        task_ids.append(task.id)

    return SentimentReanalysisResponse(
        dispatched=len(task_ids),
        task_ids=task_ids,
        skipped_article_ids=skipped,
    )
