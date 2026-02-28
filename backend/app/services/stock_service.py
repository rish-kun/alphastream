from __future__ import annotations

from sqlalchemy import String, and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.models.news import ArticleStockMention, NewsArticle
from app.models.sentiment import AlphaMetric
from app.models.stock import Stock
from app.schemas.stock import StockDetail, StockResponse, StockSearchResponse


class StockService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def search_stocks(self, query: str, limit: int = 20) -> StockSearchResponse:
        """Search stocks by ticker or company name."""
        pattern = f"%{query}%"
        stmt = (
            select(Stock)
            .where(
                or_(
                    Stock.ticker.ilike(pattern),
                    Stock.company_name.ilike(pattern),
                    Stock.aliases.cast(String).ilike(pattern),
                )
            )
            .order_by(Stock.ticker)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        stocks = result.scalars().all()

        # Count total matches
        count_stmt = (
            select(func.count())
            .select_from(Stock)
            .where(
                or_(
                    Stock.ticker.ilike(pattern),
                    Stock.company_name.ilike(pattern),
                    Stock.aliases.cast(String).ilike(pattern),
                )
            )
        )
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()

        return StockSearchResponse(
            results=[StockResponse.model_validate(s) for s in stocks],
            total=total,
            query=query,
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
    ) -> dict:
        """Get news articles related to a stock."""
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

        # Fetch paginated articles
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
        )
        articles_result = await self.db.execute(articles_stmt)
        articles = articles_result.scalars().all()

        return {
            "articles": [
                {
                    "id": str(a.id),
                    "title": a.title,
                    "summary": a.summary,
                    "url": a.url,
                    "source": a.source,
                    "published_at": a.published_at.isoformat(),
                    "category": a.category,
                }
                for a in articles
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

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
