from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.stock import StockResponse


class PortfolioCreate(BaseModel):
    name: str


class PortfolioUpdate(BaseModel):
    name: str


class PortfolioStockAdd(BaseModel):
    ticker: str
    quantity: float | None = None
    avg_buy_price: float | None = None


class PortfolioStockResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    stock: StockResponse
    quantity: float | None = None
    avg_buy_price: float | None = None
    added_at: datetime


class PortfolioResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    created_at: datetime


class PortfolioDetail(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    stocks: list[PortfolioStockResponse] = []
    created_at: datetime
