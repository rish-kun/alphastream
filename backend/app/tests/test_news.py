"""Tests for news API endpoints."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.core.exceptions import NotFoundError
from app.schemas.news import NewsArticleResponse, NewsListResponse


def _make_article_response(**overrides) -> NewsArticleResponse:
    defaults = {
        "id": uuid.uuid4(),
        "title": "Sensex rises 500 points on banking rally",
        "summary": "Indian markets surged on Monday...",
        "url": "https://example.com/article/1",
        "source": "moneycontrol",
        "published_at": datetime.now(UTC),
        "category": "markets",
    }
    defaults.update(overrides)
    return NewsArticleResponse(**defaults)


class TestGetNewsFeed:
    async def test_returns_paginated_feed(
        self, client: AsyncClient, mock_db: AsyncMock
    ):
        article = _make_article_response()

        with patch("app.api.v1.news.NewsService") as MockService:
            instance = MockService.return_value
            instance.get_news_feed = AsyncMock(
                return_value=NewsListResponse(
                    articles=[article],
                    total=1,
                    page=1,
                    page_size=20,
                )
            )

            resp = await client.get("/api/v1/news/")

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["page"] == 1
        assert len(data["articles"]) == 1
        assert data["articles"][0]["title"] == article.title

    async def test_filter_by_source(self, client: AsyncClient, mock_db: AsyncMock):
        with patch("app.api.v1.news.NewsService") as MockService:
            instance = MockService.return_value
            instance.get_news_feed = AsyncMock(
                return_value=NewsListResponse(
                    articles=[],
                    total=0,
                    page=1,
                    page_size=20,
                )
            )

            resp = await client.get("/api/v1/news/?source=moneycontrol")

        assert resp.status_code == 200

    async def test_pagination_params(self, client: AsyncClient, mock_db: AsyncMock):
        with patch("app.api.v1.news.NewsService") as MockService:
            instance = MockService.return_value
            instance.get_news_feed = AsyncMock(
                return_value=NewsListResponse(
                    articles=[],
                    total=0,
                    page=2,
                    page_size=10,
                )
            )

            resp = await client.get("/api/v1/news/?page=2&page_size=10")

        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 2
        assert data["page_size"] == 10

    async def test_invalid_page(self, client: AsyncClient):
        resp = await client.get("/api/v1/news/?page=0")
        assert resp.status_code == 422

    async def test_invalid_page_size(self, client: AsyncClient):
        resp = await client.get("/api/v1/news/?page_size=100")
        assert resp.status_code == 422


class TestGetTrendingNews:
    async def test_returns_trending(self, client: AsyncClient, mock_db: AsyncMock):
        articles = [_make_article_response() for _ in range(3)]

        with patch("app.api.v1.news.NewsService") as MockService:
            instance = MockService.return_value
            instance.get_trending_news = AsyncMock(return_value=articles)

            resp = await client.get("/api/v1/news/trending")

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3

    async def test_limit_param(self, client: AsyncClient, mock_db: AsyncMock):
        with patch("app.api.v1.news.NewsService") as MockService:
            instance = MockService.return_value
            instance.get_trending_news = AsyncMock(return_value=[])

            resp = await client.get("/api/v1/news/trending?limit=5")

        assert resp.status_code == 200


class TestGetArticle:
    async def test_get_article_found(self, client: AsyncClient, mock_db: AsyncMock):
        article_id = uuid.uuid4()
        article = _make_article_response(id=article_id)

        with patch("app.api.v1.news.NewsService") as MockService:
            instance = MockService.return_value
            instance.get_article = AsyncMock(return_value=article)

            resp = await client.get(f"/api/v1/news/{article_id}")

        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(article_id)

    async def test_get_article_not_found(self, client: AsyncClient, mock_db: AsyncMock):
        article_id = uuid.uuid4()

        with patch("app.api.v1.news.NewsService") as MockService:
            instance = MockService.return_value
            instance.get_article = AsyncMock(
                side_effect=NotFoundError("Article", str(article_id))
            )

            resp = await client.get(f"/api/v1/news/{article_id}")

        assert resp.status_code == 404

    async def test_invalid_uuid(self, client: AsyncClient):
        resp = await client.get("/api/v1/news/not-a-uuid")
        assert resp.status_code == 422
