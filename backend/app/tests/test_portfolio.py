"""Tests for portfolio API endpoints (all auth-protected)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.schemas.portfolio import PortfolioResponse
from app.tests.conftest import TEST_USER_ID


def _make_portfolio_response(**overrides) -> PortfolioResponse:
    defaults = {
        "id": uuid.uuid4(),
        "name": "My Portfolio",
        "created_at": datetime.now(UTC),
    }
    defaults.update(overrides)
    return PortfolioResponse(**defaults)


class TestListPortfolios:
    async def test_returns_empty_list(
        self, client: AsyncClient, mock_db: AsyncMock, auth_headers: dict
    ):
        with patch("app.api.v1.portfolio.PortfolioService") as MockService:
            instance = MockService.return_value
            instance.list_portfolios = AsyncMock(return_value=[])

            resp = await client.get("/api/v1/portfolios/", headers=auth_headers)

        assert resp.status_code == 200
        assert resp.json() == []

    async def test_returns_portfolios(
        self, client: AsyncClient, mock_db: AsyncMock, auth_headers: dict
    ):
        portfolios = [
            _make_portfolio_response(name="Portfolio 1"),
            _make_portfolio_response(name="Portfolio 2"),
        ]

        with patch("app.api.v1.portfolio.PortfolioService") as MockService:
            instance = MockService.return_value
            instance.list_portfolios = AsyncMock(return_value=portfolios)

            resp = await client.get("/api/v1/portfolios/", headers=auth_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2


class TestCreatePortfolio:
    async def test_create_success(
        self, client: AsyncClient, mock_db: AsyncMock, auth_headers: dict
    ):
        portfolio = _make_portfolio_response(name="New Portfolio")

        with patch("app.api.v1.portfolio.PortfolioService") as MockService:
            instance = MockService.return_value
            instance.create_portfolio = AsyncMock(return_value=portfolio)

            resp = await client.post(
                "/api/v1/portfolios/",
                json={"name": "New Portfolio"},
                headers=auth_headers,
            )

        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "New Portfolio"

    async def test_create_missing_name(self, client: AsyncClient, auth_headers: dict):
        resp = await client.post("/api/v1/portfolios/", json={}, headers=auth_headers)
        assert resp.status_code == 422


class TestUpdatePortfolio:
    async def test_update_success(
        self, client: AsyncClient, mock_db: AsyncMock, auth_headers: dict
    ):
        pid = uuid.uuid4()
        updated = _make_portfolio_response(id=pid, name="Updated Name")

        with patch("app.api.v1.portfolio.PortfolioService") as MockService:
            instance = MockService.return_value
            instance.update_portfolio = AsyncMock(return_value=updated)

            resp = await client.put(
                f"/api/v1/portfolios/{pid}",
                json={"name": "Updated Name"},
                headers=auth_headers,
            )

        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Name"

    async def test_update_not_found(
        self, client: AsyncClient, mock_db: AsyncMock, auth_headers: dict
    ):
        pid = uuid.uuid4()

        with patch("app.api.v1.portfolio.PortfolioService") as MockService:
            instance = MockService.return_value
            instance.update_portfolio = AsyncMock(
                side_effect=NotFoundError("Portfolio", str(pid))
            )

            resp = await client.put(
                f"/api/v1/portfolios/{pid}",
                json={"name": "Updated"},
                headers=auth_headers,
            )

        assert resp.status_code == 404

    async def test_update_forbidden(
        self, client: AsyncClient, mock_db: AsyncMock, auth_headers: dict
    ):
        pid = uuid.uuid4()

        with patch("app.api.v1.portfolio.PortfolioService") as MockService:
            instance = MockService.return_value
            instance.update_portfolio = AsyncMock(
                side_effect=ForbiddenError("You do not have access")
            )

            resp = await client.put(
                f"/api/v1/portfolios/{pid}",
                json={"name": "Updated"},
                headers=auth_headers,
            )

        assert resp.status_code == 403


class TestDeletePortfolio:
    async def test_delete_success(
        self, client: AsyncClient, mock_db: AsyncMock, auth_headers: dict
    ):
        pid = uuid.uuid4()

        with patch("app.api.v1.portfolio.PortfolioService") as MockService:
            instance = MockService.return_value
            instance.delete_portfolio = AsyncMock(return_value=None)

            resp = await client.delete(
                f"/api/v1/portfolios/{pid}", headers=auth_headers
            )

        assert resp.status_code == 204

    async def test_delete_not_found(
        self, client: AsyncClient, mock_db: AsyncMock, auth_headers: dict
    ):
        pid = uuid.uuid4()

        with patch("app.api.v1.portfolio.PortfolioService") as MockService:
            instance = MockService.return_value
            instance.delete_portfolio = AsyncMock(
                side_effect=NotFoundError("Portfolio", str(pid))
            )

            resp = await client.delete(
                f"/api/v1/portfolios/{pid}", headers=auth_headers
            )

        assert resp.status_code == 404


class TestAddStock:
    async def test_add_stock_success(
        self, client: AsyncClient, mock_db: AsyncMock, auth_headers: dict
    ):
        pid = uuid.uuid4()

        with patch("app.api.v1.portfolio.PortfolioService") as MockService:
            instance = MockService.return_value
            instance.add_stock = AsyncMock(
                return_value={
                    "id": str(uuid.uuid4()),
                    "stock": {
                        "id": str(uuid.uuid4()),
                        "ticker": "RELIANCE",
                        "exchange": "NSE",
                        "company_name": "Reliance Industries",
                        "sector": "Energy",
                        "industry": "Oil & Gas",
                        "last_price": 2450.50,
                    },
                    "quantity": 10.0,
                    "avg_buy_price": 2400.0,
                    "added_at": datetime.now(UTC).isoformat(),
                }
            )

            resp = await client.post(
                f"/api/v1/portfolios/{pid}/stocks",
                json={
                    "ticker": "RELIANCE",
                    "quantity": 10.0,
                    "avg_buy_price": 2400.0,
                },
                headers=auth_headers,
            )

        assert resp.status_code == 201
        data = resp.json()
        assert data["stock"]["ticker"] == "RELIANCE"
        assert data["quantity"] == 10.0

    async def test_add_stock_already_exists(
        self, client: AsyncClient, mock_db: AsyncMock, auth_headers: dict
    ):
        pid = uuid.uuid4()

        with patch("app.api.v1.portfolio.PortfolioService") as MockService:
            instance = MockService.return_value
            instance.add_stock = AsyncMock(
                side_effect=ConflictError("Stock already in portfolio")
            )

            resp = await client.post(
                f"/api/v1/portfolios/{pid}/stocks",
                json={"ticker": "RELIANCE"},
                headers=auth_headers,
            )

        assert resp.status_code == 409

    async def test_add_stock_missing_ticker(
        self, client: AsyncClient, auth_headers: dict
    ):
        pid = uuid.uuid4()
        resp = await client.post(
            f"/api/v1/portfolios/{pid}/stocks", json={}, headers=auth_headers
        )
        assert resp.status_code == 422


class TestRemoveStock:
    async def test_remove_stock_success(
        self, client: AsyncClient, mock_db: AsyncMock, auth_headers: dict
    ):
        pid = uuid.uuid4()

        with patch("app.api.v1.portfolio.PortfolioService") as MockService:
            instance = MockService.return_value
            instance.remove_stock = AsyncMock(return_value=None)

            resp = await client.delete(
                f"/api/v1/portfolios/{pid}/stocks/RELIANCE",
                headers=auth_headers,
            )

        assert resp.status_code == 204

    async def test_remove_stock_not_found(
        self, client: AsyncClient, mock_db: AsyncMock, auth_headers: dict
    ):
        pid = uuid.uuid4()

        with patch("app.api.v1.portfolio.PortfolioService") as MockService:
            instance = MockService.return_value
            instance.remove_stock = AsyncMock(
                side_effect=NotFoundError("PortfolioStock", "INVALID")
            )

            resp = await client.delete(
                f"/api/v1/portfolios/{pid}/stocks/INVALID",
                headers=auth_headers,
            )

        assert resp.status_code == 404


class TestGetPortfolioNews:
    async def test_returns_news(
        self, client: AsyncClient, mock_db: AsyncMock, auth_headers: dict
    ):
        pid = uuid.uuid4()

        with patch("app.api.v1.portfolio.PortfolioService") as MockService:
            instance = MockService.return_value
            instance.get_portfolio_news = AsyncMock(
                return_value={
                    "portfolio_id": str(pid),
                    "articles": [],
                }
            )

            resp = await client.get(
                f"/api/v1/portfolios/{pid}/news", headers=auth_headers
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["portfolio_id"] == str(pid)


class TestGetPortfolioAlpha:
    async def test_returns_alpha(
        self, client: AsyncClient, mock_db: AsyncMock, auth_headers: dict
    ):
        pid = uuid.uuid4()

        with patch("app.api.v1.portfolio.PortfolioService") as MockService:
            instance = MockService.return_value
            instance.get_portfolio_alpha = AsyncMock(
                return_value={
                    "portfolio_id": str(pid),
                    "metrics": [],
                }
            )

            resp = await client.get(
                f"/api/v1/portfolios/{pid}/alpha", headers=auth_headers
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["metrics"] == []
