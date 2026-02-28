from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class NewsArticleResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    title: str
    summary: str | None = None
    url: str
    source: str
    published_at: datetime
    category: str | None = None


class NewsListResponse(BaseModel):
    articles: list[NewsArticleResponse]
    total: int
    page: int
    page_size: int


class NewsFeedQuery(BaseModel):
    page: int = 1
    page_size: int = 20
    source: str | None = None
    category: str | None = None
    ticker: str | None = None
    from_date: datetime | None = None
    to_date: datetime | None = None
