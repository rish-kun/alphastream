"""Tests for stock API endpoints."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.core.exceptions import NotFoundError
from app.tests.conftest import MockResult


def _make_stock(**overrides):
    """Create a mock Stock-like object."""
    from types import SimpleNamespace

    defaults = {
        "id": uuid.uuid4(),
        "ticker": "RELIANCE",
        "exchange": "NSE",
        "company_name": "Reliance Industries Ltd",
        "sector": "Energy",
        "industry": "Oil & Gas",
        "market_cap": 1_800_000_000_000,
        "aliases": ["RIL"],
        "last_price": Decimal("2450.50"),
        "price_updated_at": datetime.now(UTC),
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class TestSearchStocks:
    async def test_search_returns_results(
        self, client: AsyncClient, mock_db: AsyncMock
    ):
        stock = _make_stock()

        with patch("app.api.v1.stocks.StockService") as MockService:
            from app.schemas.stock import StockResponse, StockSearchResponse

            instance = MockService.return_value
            instance.search_stocks = AsyncMock(
                return_value=StockSearchResponse(
                    results=[
                        StockResponse(
                            id=stock.id,
                            ticker=stock.ticker,
                            exchange=stock.exchange,
                            company_name=stock.company_name,
                            sector=stock.sector,
                            industry=stock.industry,
                            last_price=float(stock.last_price),
                        )
                    ],
                    total=1,
                    query="RELIANCE",
                )
            )

            resp = await client.get("/api/v1/stocks/search?q=RELIANCE")

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["query"] == "RELIANCE"
        assert len(data["results"]) == 1
        assert data["results"][0]["ticker"] == "RELIANCE"

    async def test_search_requires_query(self, client: AsyncClient):
        resp = await client.get("/api/v1/stocks/search")
        assert resp.status_code == 422

    async def test_search_limit_validation(self, client: AsyncClient):
        resp = await client.get("/api/v1/stocks/search?q=test&limit=0")
        assert resp.status_code == 422

        resp = await client.get("/api/v1/stocks/search?q=test&limit=100")
        assert resp.status_code == 422


class TestGetSectors:
    async def test_returns_sector_list(self, client: AsyncClient, mock_db: AsyncMock):
        mock_db.execute.return_value = MockResult(
            data=[("Banking & Finance",), ("Energy",), ("IT",)]
        )

        resp = await client.get("/api/v1/stocks/sectors")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 3
        assert "Energy" in data


class TestGetStock:
    async def test_get_stock_found(self, client: AsyncClient, mock_db: AsyncMock):
        stock = _make_stock()

        with patch("app.api.v1.stocks.StockService") as MockService:
            from app.schemas.stock import StockDetail

            instance = MockService.return_value
            instance.get_stock = AsyncMock(
                return_value=StockDetail(
                    id=stock.id,
                    ticker=stock.ticker,
                    exchange=stock.exchange,
                    company_name=stock.company_name,
                    sector=stock.sector,
                    industry=stock.industry,
                    market_cap=stock.market_cap,
                    aliases=stock.aliases,
                    last_price=float(stock.last_price),
                    price_updated_at=stock.price_updated_at,
                )
            )

            resp = await client.get("/api/v1/stocks/RELIANCE")

        assert resp.status_code == 200
        data = resp.json()
        assert data["ticker"] == "RELIANCE"
        assert data["company_name"] == "Reliance Industries Ltd"
        assert data["sector"] == "Energy"

    async def test_get_stock_not_found(self, client: AsyncClient, mock_db: AsyncMock):
        with patch("app.api.v1.stocks.StockService") as MockService:
            instance = MockService.return_value
            instance.get_stock = AsyncMock(
                side_effect=NotFoundError("Stock", "INVALID")
            )

            resp = await client.get("/api/v1/stocks/INVALID")

        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()


class TestGetStockNews:
    async def test_returns_paginated_news(
        self, client: AsyncClient, mock_db: AsyncMock
    ):
        with patch("app.api.v1.stocks.StockService") as MockService:
            instance = MockService.return_value
            instance.get_stock_news = AsyncMock(
                return_value={
                    "articles": [],
                    "total": 0,
                    "page": 1,
                    "page_size": 20,
                }
            )

            resp = await client.get("/api/v1/stocks/RELIANCE/news")

        assert resp.status_code == 200
        data = resp.json()
        assert "articles" in data
        assert data["total"] == 0


class TestGetStockAlpha:
    async def test_returns_alpha_metrics(self, client: AsyncClient, mock_db: AsyncMock):
        with patch("app.api.v1.stocks.StockService") as MockService:
            instance = MockService.return_value
            instance.get_stock_alpha = AsyncMock(
                return_value={"stock": "RELIANCE", "metrics": []}
            )

            resp = await client.get("/api/v1/stocks/RELIANCE/alpha")

        assert resp.status_code == 200
        data = resp.json()
        assert data["stock"] == "RELIANCE"
        assert data["metrics"] == []
