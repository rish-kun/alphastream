from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.news import ArticleStockMention, NewsArticle
from app.models.sentiment import AlphaMetric, SentimentAnalysis
from app.models.stock import Stock
from app.schemas.sentiment import (
    AlphaMetricResponse,
    SectorSentiment,
    SentimentOverview,
)

router = APIRouter(prefix="/sentiment", tags=["sentiment"])


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
