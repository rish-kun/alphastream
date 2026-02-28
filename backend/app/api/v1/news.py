from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.news import NewsArticleResponse, NewsFeedQuery, NewsListResponse
from app.services.news_service import NewsService

router = APIRouter(prefix="/news", tags=["news"])


@router.get("/", response_model=NewsListResponse)
async def get_news_feed(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 20,
    source: Annotated[str | None, Query()] = None,
    category: Annotated[str | None, Query()] = None,
    ticker: Annotated[str | None, Query()] = None,
    from_date: Annotated[datetime | None, Query()] = None,
    to_date: Annotated[datetime | None, Query()] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> NewsListResponse:
    query = NewsFeedQuery(
        page=page,
        page_size=page_size,
        source=source,
        category=category,
        ticker=ticker,
        from_date=from_date,
        to_date=to_date,
    )
    service = NewsService(db)
    return await service.get_news_feed(query)


@router.get("/trending", response_model=list[NewsArticleResponse])
async def get_trending_news(
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> list[NewsArticleResponse]:
    service = NewsService(db)
    return await service.get_trending_news(limit)


@router.get("/{id}", response_model=NewsArticleResponse)
async def get_article(
    id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> NewsArticleResponse:
    service = NewsService(db)
    return await service.get_article(id)
