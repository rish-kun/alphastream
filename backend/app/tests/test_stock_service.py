"""Unit tests for StockService ranking/search behavior."""

from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services.stock_service import StockService
from app.tests.conftest import MockResult


def _make_stock(**overrides):
    defaults = {
        "id": uuid.uuid4(),
        "ticker": "RELIANCE",
        "exchange": "NSE",
        "company_name": "Reliance Industries Ltd",
        "sector": "Energy",
        "industry": "Oil & Gas",
        "last_price": 2450.5,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


@pytest.mark.asyncio
async def test_search_stocks_empty_query_uses_article_count_ordering():
    stock = _make_stock()
    mock_db = AsyncMock()
    executed_statements = []

    async def execute_side_effect(stmt):
        executed_statements.append(stmt)
        if len(executed_statements) == 1:
            return MockResult(data=[stock])
        return MockResult(scalar=1)

    mock_db.execute = AsyncMock(side_effect=execute_side_effect)

    service = StockService(mock_db)
    result = await service.search_stocks("", limit=10)

    assert len(result.results) == 1
    assert result.results[0].ticker == "RELIANCE"

    first_sql = str(executed_statements[0]).lower()
    assert "article_stock_mentions" in first_sql
    assert "coalesce" in first_sql


@pytest.mark.asyncio
async def test_search_stocks_query_filters_by_text():
    stock = _make_stock(ticker="TCS", company_name="Tata Consultancy Services")
    mock_db = AsyncMock()
    executed_statements = []

    async def execute_side_effect(stmt):
        executed_statements.append(stmt)
        if len(executed_statements) == 1:
            return MockResult(data=[stock])
        return MockResult(scalar=1)

    mock_db.execute = AsyncMock(side_effect=execute_side_effect)

    service = StockService(mock_db)
    result = await service.search_stocks("tata", limit=10)

    assert len(result.results) == 1
    assert result.results[0].ticker == "TCS"

    first_sql = str(executed_statements[0]).lower()
    assert "article_stock_mentions" not in first_sql
    assert "like lower" in first_sql
