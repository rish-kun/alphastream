from __future__ import annotations

import uuid

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.news import ArticleStockMention, NewsArticle
from app.models.portfolio import Portfolio, PortfolioStock
from app.models.sentiment import AlphaMetric
from app.models.stock import Stock
from app.schemas.portfolio import (
    PortfolioCreate,
    PortfolioDetail,
    PortfolioResponse,
    PortfolioStockResponse,
    PortfolioUpdate,
)
from app.schemas.stock import StockResponse


class PortfolioService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _get_portfolio_for_user(
        self, user_id: uuid.UUID, portfolio_id: uuid.UUID
    ) -> Portfolio:
        """Helper to fetch a portfolio and verify ownership."""
        stmt = select(Portfolio).where(Portfolio.id == portfolio_id)
        result = await self.db.execute(stmt)
        portfolio = result.scalar_one_or_none()

        if portfolio is None:
            raise NotFoundError("Portfolio", str(portfolio_id))

        if portfolio.user_id != user_id:
            raise ForbiddenError("You do not have access to this portfolio")

        return portfolio

    async def list_portfolios(self, user_id: uuid.UUID) -> list[PortfolioResponse]:
        """List all portfolios for a user."""
        stmt = (
            select(Portfolio)
            .where(Portfolio.user_id == user_id)
            .order_by(Portfolio.created_at.desc())
        )
        result = await self.db.execute(stmt)
        portfolios = result.scalars().all()

        return [PortfolioResponse.model_validate(p) for p in portfolios]

    async def create_portfolio(
        self, user_id: uuid.UUID, data: PortfolioCreate
    ) -> PortfolioResponse:
        """Create a new portfolio."""
        portfolio = Portfolio(
            user_id=user_id,
            name=data.name,
        )
        self.db.add(portfolio)
        await self.db.flush()
        await self.db.refresh(portfolio)

        return PortfolioResponse.model_validate(portfolio)

    async def update_portfolio(
        self,
        user_id: uuid.UUID,
        portfolio_id: uuid.UUID,
        data: PortfolioUpdate,
    ) -> PortfolioResponse:
        """Update a portfolio."""
        portfolio = await self._get_portfolio_for_user(user_id, portfolio_id)
        portfolio.name = data.name
        await self.db.flush()
        await self.db.refresh(portfolio)

        return PortfolioResponse.model_validate(portfolio)

    async def delete_portfolio(
        self, user_id: uuid.UUID, portfolio_id: uuid.UUID
    ) -> None:
        """Delete a portfolio."""
        portfolio = await self._get_portfolio_for_user(user_id, portfolio_id)
        await self.db.delete(portfolio)
        await self.db.flush()

    async def add_stock(
        self,
        user_id: uuid.UUID,
        portfolio_id: uuid.UUID,
        ticker: str,
        quantity: float | None = None,
        avg_buy_price: float | None = None,
    ) -> dict:
        """Add a stock to a portfolio."""
        portfolio = await self._get_portfolio_for_user(user_id, portfolio_id)

        # Find stock by ticker
        stock_stmt = select(Stock).where(func.lower(Stock.ticker) == func.lower(ticker))
        stock_result = await self.db.execute(stock_stmt)
        stock = stock_result.scalar_one_or_none()

        if stock is None:
            raise NotFoundError("Stock", ticker)

        # Check if stock already in portfolio
        existing_stmt = select(PortfolioStock).where(
            and_(
                PortfolioStock.portfolio_id == portfolio_id,
                PortfolioStock.stock_id == stock.id,
            )
        )
        existing_result = await self.db.execute(existing_stmt)
        if existing_result.scalar_one_or_none() is not None:
            raise ConflictError(f"Stock '{ticker}' is already in this portfolio")

        # Create PortfolioStock
        ps = PortfolioStock(
            portfolio_id=portfolio_id,
            stock_id=stock.id,
            quantity=quantity,
            avg_buy_price=avg_buy_price,
        )
        self.db.add(ps)
        await self.db.flush()
        await self.db.refresh(ps)

        return {
            "id": str(ps.id),
            "stock": StockResponse.model_validate(stock).model_dump(),
            "quantity": float(ps.quantity) if ps.quantity is not None else None,
            "avg_buy_price": float(ps.avg_buy_price)
            if ps.avg_buy_price is not None
            else None,
            "added_at": ps.added_at.isoformat(),
        }

    async def remove_stock(
        self, user_id: uuid.UUID, portfolio_id: uuid.UUID, ticker: str
    ) -> None:
        """Remove a stock from a portfolio."""
        await self._get_portfolio_for_user(user_id, portfolio_id)

        # Find stock by ticker
        stock_stmt = select(Stock).where(func.lower(Stock.ticker) == func.lower(ticker))
        stock_result = await self.db.execute(stock_stmt)
        stock = stock_result.scalar_one_or_none()

        if stock is None:
            raise NotFoundError("Stock", ticker)

        # Find the PortfolioStock entry
        ps_stmt = select(PortfolioStock).where(
            and_(
                PortfolioStock.portfolio_id == portfolio_id,
                PortfolioStock.stock_id == stock.id,
            )
        )
        ps_result = await self.db.execute(ps_stmt)
        ps = ps_result.scalar_one_or_none()

        if ps is None:
            raise NotFoundError("PortfolioStock", ticker)

        await self.db.delete(ps)
        await self.db.flush()

    async def get_portfolio_news(
        self, user_id: uuid.UUID, portfolio_id: uuid.UUID
    ) -> dict:
        """Get news related to stocks in a portfolio."""
        portfolio = await self._get_portfolio_for_user(user_id, portfolio_id)

        # Get all stock_ids in this portfolio
        stock_ids_stmt = select(PortfolioStock.stock_id).where(
            PortfolioStock.portfolio_id == portfolio_id
        )
        stock_ids_result = await self.db.execute(stock_ids_stmt)
        stock_ids = [row[0] for row in stock_ids_result.all()]

        if not stock_ids:
            return {"portfolio_id": str(portfolio_id), "articles": []}

        # Get recent news articles mentioning those stocks
        articles_stmt = (
            select(NewsArticle)
            .join(
                ArticleStockMention,
                ArticleStockMention.article_id == NewsArticle.id,
            )
            .where(ArticleStockMention.stock_id.in_(stock_ids))
            .order_by(NewsArticle.published_at.desc())
            .limit(50)
        )
        articles_result = await self.db.execute(articles_stmt)
        articles = articles_result.scalars().unique().all()

        return {
            "portfolio_id": str(portfolio_id),
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
        }

    async def get_portfolio_alpha(
        self, user_id: uuid.UUID, portfolio_id: uuid.UUID
    ) -> dict:
        """Get alpha metrics for a portfolio."""
        portfolio = await self._get_portfolio_for_user(user_id, portfolio_id)

        # Get all stock_ids in this portfolio
        stock_ids_stmt = select(PortfolioStock.stock_id).where(
            PortfolioStock.portfolio_id == portfolio_id
        )
        stock_ids_result = await self.db.execute(stock_ids_stmt)
        stock_ids = [row[0] for row in stock_ids_result.all()]

        if not stock_ids:
            return {"portfolio_id": str(portfolio_id), "metrics": []}

        # Get latest alpha metrics for those stocks
        metrics_stmt = (
            select(AlphaMetric)
            .where(AlphaMetric.stock_id.in_(stock_ids))
            .order_by(AlphaMetric.computed_at.desc())
            .limit(100)
        )
        metrics_result = await self.db.execute(metrics_stmt)
        metrics = metrics_result.scalars().all()

        return {
            "portfolio_id": str(portfolio_id),
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
