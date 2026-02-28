from __future__ import annotations

import uuid

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.news import ArticleStockMention, NewsArticle
from app.models.sentiment import SentimentAnalysis
from app.models.stock import Stock
from app.schemas.news import NewsArticleResponse, NewsFeedQuery, NewsListResponse


class NewsService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_news_feed(self, query: NewsFeedQuery) -> NewsListResponse:
        """Get paginated news feed with optional filters."""
        base_stmt = select(NewsArticle)
        count_stmt = select(func.count()).select_from(NewsArticle)

        conditions = []

        if query.source:
            conditions.append(NewsArticle.source == query.source)

        if query.category:
            conditions.append(NewsArticle.category == query.category)

        if query.from_date:
            conditions.append(NewsArticle.published_at >= query.from_date)

        if query.to_date:
            conditions.append(NewsArticle.published_at <= query.to_date)

        if query.ticker:
            # Join through article_stock_mentions to filter by ticker
            base_stmt = base_stmt.join(
                ArticleStockMention,
                ArticleStockMention.article_id == NewsArticle.id,
            ).join(
                Stock,
                Stock.id == ArticleStockMention.stock_id,
            )
            count_stmt = count_stmt.join(
                ArticleStockMention,
                ArticleStockMention.article_id == NewsArticle.id,
            ).join(
                Stock,
                Stock.id == ArticleStockMention.stock_id,
            )
            conditions.append(func.lower(Stock.ticker) == func.lower(query.ticker))

        if conditions:
            base_stmt = base_stmt.where(and_(*conditions))
            count_stmt = count_stmt.where(and_(*conditions))

        # Get total count
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()

        # Paginate
        offset = (query.page - 1) * query.page_size
        articles_stmt = (
            base_stmt.order_by(NewsArticle.published_at.desc())
            .offset(offset)
            .limit(query.page_size)
        )
        articles_result = await self.db.execute(articles_stmt)
        articles = articles_result.scalars().all()

        return NewsListResponse(
            articles=[NewsArticleResponse.model_validate(a) for a in articles],
            total=total,
            page=query.page,
            page_size=query.page_size,
        )

    async def get_trending_news(self, limit: int = 10) -> list[NewsArticleResponse]:
        """Get trending news articles (most recent with sentiment analyses)."""
        stmt = (
            select(NewsArticle)
            .join(
                SentimentAnalysis,
                SentimentAnalysis.article_id == NewsArticle.id,
            )
            .order_by(NewsArticle.published_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        articles = result.scalars().unique().all()

        return [NewsArticleResponse.model_validate(a) for a in articles]

    async def get_article(self, article_id: uuid.UUID) -> NewsArticleResponse:
        """Get a specific news article by ID."""
        stmt = select(NewsArticle).where(NewsArticle.id == article_id)
        result = await self.db.execute(stmt)
        article = result.scalar_one_or_none()

        if article is None:
            raise NotFoundError("Article", str(article_id))

        return NewsArticleResponse.model_validate(article)
