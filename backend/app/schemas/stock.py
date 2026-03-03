from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class StockResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    ticker: str
    exchange: str
    company_name: str
    sector: str
    industry: str
    last_price: float | None = None


class StockSearchResponse(BaseModel):
    results: list[StockResponse]
    total: int
    query: str


class StockDetail(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    ticker: str
    exchange: str
    company_name: str
    sector: str
    industry: str
    market_cap: int | None = None
    aliases: list[str] = []
    last_price: float | None = None
    price_updated_at: datetime | None = None


class StockNewsItem(BaseModel):
    """News article for a specific stock with sentiment analysis."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    title: str
    summary: str | None = None
    url: str
    source: str
    published_at: datetime
    category: str | None = None
    sentiment_score: float | None = None
    confidence: float | None = None
    impact_timeline: str | None = None


class StockNewsResponse(BaseModel):
    """Response for stock news endpoint with sentiment data."""

    articles: list[StockNewsItem]
    total: int
    page: int
    page_size: int
