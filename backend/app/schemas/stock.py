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
