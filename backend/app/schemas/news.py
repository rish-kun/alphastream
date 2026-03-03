from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

if TYPE_CHECKING:
    from app.schemas.sentiment import SentimentResponse


class NewsMention(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    stock_id: uuid.UUID
    ticker: str = ""
    company_name: str = ""
    relevance_score: float
    mentioned_as: str
    impact_direction: str

    @classmethod
    def model_validate(cls, obj: Any, **kwargs: Any) -> "NewsMention":
        """Override to extract ticker/company_name from the stock relationship."""
        instance = super().model_validate(obj, **kwargs)
        # If the ORM object has a `stock` relationship loaded, pull fields from it
        if hasattr(obj, "stock") and obj.stock is not None:
            instance.ticker = getattr(obj.stock, "ticker", "")
            instance.company_name = getattr(obj.stock, "company_name", "")
        return instance


class NewsArticleResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    title: str
    summary: str | None = None
    url: str
    source: str
    published_at: datetime
    category: str | None = None
    mentions: list[NewsMention] = []
    sentiment_analyses: list[SentimentResponse] = []


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
    search: str | None = None
    from_date: datetime | None = None
    to_date: datetime | None = None


from app.schemas.sentiment import SentimentResponse

NewsArticleResponse.model_rebuild()
