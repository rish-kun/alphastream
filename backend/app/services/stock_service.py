from __future__ import annotations

from sqlalchemy import String, and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.models.news import ArticleStockMention, NewsArticle
from app.models.sentiment import AlphaMetric, SentimentAnalysis
from app.models.stock import Stock
from app.schemas.stock import (
    StockDetail,
    StockNewsResponse,
    StockResponse,
    StockSearchResponse,
)


class StockService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def search_stocks(
        self,
        query: str | None = None,
        limit: int = 20,
        sector: str | None = None,
        industry: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        min_market_cap: int | None = None,
        max_market_cap: int | None = None,
    ) -> StockSearchResponse:
        """Search stocks by ticker, company name, and/or filter by data fields."""
        conditions = []

        if query and query.strip():
            normalized_query = query.strip()
            pattern = f"%{normalized_query}%"
            conditions.append(
                or_(
                    Stock.ticker.ilike(pattern),
                    Stock.company_name.ilike(pattern),
                    Stock.aliases.cast(String).ilike(pattern),
                )
            )

        if sector:
            conditions.append(Stock.sector == sector)

        if industry:
            conditions.append(Stock.industry == industry)

        if min_price is not None:
            conditions.append(Stock.last_price >= min_price)

        if max_price is not None:
            conditions.append(Stock.last_price <= max_price)

        if min_market_cap is not None:
            conditions.append(Stock.market_cap >= min_market_cap)

        if max_market_cap is not None:
            conditions.append(Stock.market_cap <= max_market_cap)

        if not conditions:
            mention_counts_subquery = (
                select(
                    ArticleStockMention.stock_id.label("stock_id"),
                    func.count(func.distinct(ArticleStockMention.article_id)).label(
                        "article_count"
                    ),
                )
                .group_by(ArticleStockMention.stock_id)
                .subquery()
            )

            stmt = (
                select(Stock)
                .outerjoin(
                    mention_counts_subquery,
                    mention_counts_subquery.c.stock_id == Stock.id,
                )
                .order_by(
                    func.coalesce(mention_counts_subquery.c.article_count, 0).desc(),
                    Stock.ticker,
                )
                .limit(limit)
            )
            count_stmt = select(func.count()).select_from(Stock)
        else:
            stmt = (
                select(Stock)
                .where(and_(*conditions))
                .order_by(Stock.ticker)
                .limit(limit)
            )
            count_stmt = (
                select(func.count()).select_from(Stock).where(and_(*conditions))
            )

        result = await self.db.execute(stmt)
        stocks = result.scalars().all()

        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()

        return StockSearchResponse(
            results=[StockResponse.model_validate(s) for s in stocks],
            total=total,
            query=query or "",
        )

    async def get_stock(self, ticker: str) -> StockDetail:
        """Get detailed information for a specific stock."""
        stmt = select(Stock).where(func.lower(Stock.ticker) == func.lower(ticker))
        result = await self.db.execute(stmt)
        stock = result.scalar_one_or_none()

        if stock is None:
            raise NotFoundError("Stock", ticker)

        return StockDetail.model_validate(stock)

    async def get_stock_news(
        self, ticker: str, page: int = 1, page_size: int = 20
    ) -> StockNewsResponse:
        """Get news articles related to a stock with sentiment analysis."""
        # Find the stock first
        stmt = select(Stock).where(func.lower(Stock.ticker) == func.lower(ticker))
        result = await self.db.execute(stmt)
        stock = result.scalar_one_or_none()

        if stock is None:
            raise NotFoundError("Stock", ticker)

        # Count total articles for this stock
        count_stmt = (
            select(func.count())
            .select_from(NewsArticle)
            .join(
                ArticleStockMention,
                ArticleStockMention.article_id == NewsArticle.id,
            )
            .where(ArticleStockMention.stock_id == stock.id)
        )
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()

        # Fetch paginated articles with sentiment analysis
        offset = (page - 1) * page_size
        articles_stmt = (
            select(NewsArticle)
            .join(
                ArticleStockMention,
                ArticleStockMention.article_id == NewsArticle.id,
            )
            .where(ArticleStockMention.stock_id == stock.id)
            .order_by(NewsArticle.published_at.desc())
            .offset(offset)
            .limit(page_size)
            .options(
                # Eager load sentiment_analyses relationship
                selectinload(NewsArticle.sentiment_analyses)
            )
        )
        articles_result = await self.db.execute(articles_stmt)
        articles = articles_result.scalars().all()

        # Build response with sentiment data
        articles_with_sentiment = []
        for article in articles:
            # Get the most recent sentiment analysis if available
            sentiment = None
            if article.sentiment_analyses:
                # Sort by analyzed_at desc and take the first one
                sentiment = sorted(
                    article.sentiment_analyses,
                    key=lambda s: s.analyzed_at,
                    reverse=True,
                )[0]

            articles_with_sentiment.append({
                "id": article.id,
                "title": article.title,
                "summary": article.summary,
                "url": article.url,
                "source": article.source,
                "published_at": article.published_at,
                "category": article.category,
                "sentiment_score": float(sentiment.sentiment_score) if sentiment else None,
                "confidence": float(sentiment.confidence) if sentiment else None,
                "impact_timeline": sentiment.impact_timeline if sentiment else None,
            })

        return StockNewsResponse(
            articles=articles_with_sentiment,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_stock_alpha(self, ticker: str) -> dict:
        """Get alpha metrics for a stock."""
        # Find the stock first
        stmt = select(Stock).where(func.lower(Stock.ticker) == func.lower(ticker))
        result = await self.db.execute(stmt)
        stock = result.scalar_one_or_none()

        if stock is None:
            raise NotFoundError("Stock", ticker)

        # Get latest alpha metrics, ordered by computed_at desc
        # Use distinct on window_hours to get only the most recent per window
        metrics_stmt = (
            select(AlphaMetric)
            .where(AlphaMetric.stock_id == stock.id)
            .order_by(
                AlphaMetric.window_hours,
                AlphaMetric.computed_at.desc(),
            )
        )
        metrics_result = await self.db.execute(metrics_stmt)
        all_metrics = metrics_result.scalars().all()

        # Deduplicate: keep only the latest per window_hours
        seen_windows: set[int] = set()
        metrics = []
        for m in all_metrics:
            if m.window_hours not in seen_windows:
                seen_windows.add(m.window_hours)
                metrics.append(m)

        return {
            "stock": stock.ticker,
            "metrics": [
                {
                    "id": str(m.id),
                    "stock_id": str(m.stock_id) if m.stock_id else None,
                    "sector": m.sector,
                    "expectation_gap": float(m.expectation_gap),
                    "narrative_velocity": float(m.narrative_velocity),
                    "sentiment_divergence": float(m.sentiment_divergence),
                    "composite_score": float(m.composite_score),
                    "signal": m.signal,
                    "conviction": float(m.conviction),
                    "computed_at": m.computed_at.isoformat(),
                    "window_hours": m.window_hours,
                }
                for m in metrics
            ],
        }
