from __future__ import annotations

import uuid

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.news import ArticleStockMention, NewsArticle
from app.models.stock import Stock
from app.schemas.news import NewsArticleResponse, NewsFeedQuery, NewsListResponse


class NewsService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_news_feed(self, query: NewsFeedQuery) -> NewsListResponse:
        """Get paginated news feed with optional filters."""
        from sqlalchemy.orm import selectinload

        base_stmt = select(NewsArticle).options(
            selectinload(NewsArticle.sentiment_analyses),
            selectinload(NewsArticle.mentions).selectinload(ArticleStockMention.stock),
        )
        count_stmt = select(func.count(func.distinct(NewsArticle.id))).select_from(
            NewsArticle
        )

        conditions = []

        if query.source:
            conditions.append(NewsArticle.source == query.source)

        if query.category:
            conditions.append(NewsArticle.category == query.category)

        if query.from_date:
            conditions.append(NewsArticle.published_at >= query.from_date)

        if query.to_date:
            conditions.append(NewsArticle.published_at <= query.to_date)

        if query.search:
            search_term = query.search.strip()
            if search_term:
                pattern = f"%{search_term}%"
                conditions.append(
                    or_(
                        NewsArticle.title.ilike(pattern),
                        NewsArticle.summary.ilike(pattern),
                        NewsArticle.full_text.ilike(pattern),
                        NewsArticle.category.ilike(pattern),
                        NewsArticle.source.ilike(pattern),
                        NewsArticle.mentions.any(
                            ArticleStockMention.stock.has(
                                or_(
                                    Stock.ticker.ilike(pattern),
                                    Stock.company_name.ilike(pattern),
                                )
                            )
                        ),
                    )
                )

        if query.ticker:
            # Optimize ticker filtering: Use EXISTS instead of JOIN to prevent duplicate rows and distinct() overhead
            conditions.append(
                NewsArticle.mentions.any(
                    ArticleStockMention.stock.has(
                        func.lower(Stock.ticker) == func.lower(query.ticker)
                    )
                )
            )

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
        """Get trending news articles (most recent, with or without sentiment analyses)."""
        from sqlalchemy.orm import selectinload

        stmt = (
            select(NewsArticle)
            .options(
                selectinload(NewsArticle.sentiment_analyses),
                selectinload(NewsArticle.mentions).selectinload(
                    ArticleStockMention.stock
                ),
            )
            .order_by(NewsArticle.published_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        articles = result.scalars().unique().all()

        return [NewsArticleResponse.model_validate(a) for a in articles]

    async def get_article(self, article_id: uuid.UUID) -> NewsArticleResponse:
        """Get a specific news article by ID."""
        from sqlalchemy.orm import selectinload

        stmt = (
            select(NewsArticle)
            .options(
                selectinload(NewsArticle.sentiment_analyses),
                selectinload(NewsArticle.mentions).selectinload(
                    ArticleStockMention.stock
                ),
            )
            .where(NewsArticle.id == article_id)
        )
        result = await self.db.execute(stmt)
        article = result.scalar_one_or_none()

        if article is None:
            raise NotFoundError("Article", str(article_id))

        return NewsArticleResponse.model_validate(article)
