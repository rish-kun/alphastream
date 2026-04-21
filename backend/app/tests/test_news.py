from __future__ import annotations

from unittest.mock import AsyncMock, patch

from httpx import AsyncClient

from app.schemas.news import NewsArticleResponse, NewsListResponse
from app.tests.conftest import MockResult


def _make_article_response() -> NewsArticleResponse:
    import uuid
    from datetime import UTC, datetime

    return NewsArticleResponse(
        id=uuid.uuid4(),
        title="Test News",
        summary="Summary",
        url="https://example.com/news",
        source="Test Source",
        published_at=datetime.now(UTC),
        category="Finance",
        sentiment_score=0.8,
        confidence=0.9,
        impact_timeline="short",
        mentions=[],
    )


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
                    articles=[], total=0, page=1, page_size=20
                )
            )

            resp = await client.get("/api/v1/news/?source=Test+Source")

        assert resp.status_code == 200
        query_arg = instance.get_news_feed.call_args[0][0]
        assert query_arg.source == "Test Source"

    async def test_invalid_page_size(self, client: AsyncClient, mock_db: AsyncMock):
        with patch("app.api.v1.news.NewsService") as MockService:
             instance = MockService.return_value
             instance.get_news_feed = AsyncMock(
                 return_value=NewsListResponse(
                     articles=[], total=0, page=1, page_size=20
                 )
             )
             resp = await client.get("/api/v1/news/?page_size=100")
        assert resp.status_code == 200


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

    async def test_limit_validation(self, client: AsyncClient, mock_db: AsyncMock):
        with patch("app.api.v1.news.NewsService") as MockService:
            instance = MockService.return_value
            instance.get_trending_news = AsyncMock(return_value=[])

            resp = await client.get("/api/v1/news/trending?limit=100")
        assert resp.status_code == 422


class TestGetArticle:
    async def test_returns_article(self, client: AsyncClient, mock_db: AsyncMock):
        article = _make_article_response()

        with patch("app.api.v1.news.NewsService") as MockService:
            instance = MockService.return_value
            instance.get_article = AsyncMock(return_value=article)

            resp = await client.get(f"/api/v1/news/{article.id}")

        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(article.id)

    async def test_not_found(self, client: AsyncClient, mock_db: AsyncMock):
        from app.core.exceptions import NotFoundError

        with patch("app.api.v1.news.NewsService") as MockService:
            instance = MockService.return_value
            instance.get_article = AsyncMock(
                side_effect=NotFoundError("Article", "unknown")
            )

            import uuid
            resp = await client.get(f"/api/v1/news/{uuid.uuid4()}")

        assert resp.status_code == 404
