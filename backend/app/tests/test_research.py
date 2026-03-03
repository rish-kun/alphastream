"""Tests for research API endpoints."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.models.news import NewsArticle
from app.models.sentiment import SentimentAnalysis


class _ScalarRows:
    def __init__(self, items):
        self._items = items

    def scalars(self):
        return self

    def all(self):
        return self._items


class TestResearchStatus:
    async def test_progress_status_includes_derived_metrics(self, client):
        started_at = (datetime.now(UTC) - timedelta(seconds=60)).isoformat()
        async_result = SimpleNamespace(
            state="PROGRESS",
            info={
                "stage": "scraping",
                "completed_queries": 1,
                "total_queries": 3,
                "articles_new_so_far": 6,
                "started_at": started_at,
            },
            result=None,
        )

        with patch(
            "app.services.research_service._celery_app.AsyncResult",
            return_value=async_result,
        ):
            resp = await client.get("/api/v1/research/status/task-1")

        assert resp.status_code == 200
        payload = resp.json()
        assert payload["status"] == "PROGRESS"
        assert payload["progress"]["percent_complete"] == 33.33
        assert payload["progress"]["elapsed_seconds"] >= 0
        assert payload["progress"]["eta_seconds"] is not None
        assert payload["progress"]["expected_new_articles_low"] is not None
        assert payload["progress"]["expected_new_articles_high"] is not None


class TestResearchResult:
    async def test_returns_research_result_summary(self, client, mock_db):
        article_id = uuid.uuid4()
        article = NewsArticle(
            id=article_id,
            title="Policy move boosts banks",
            summary="Summary",
            full_text="Full text",
            url="https://example.com/article-1",
            source="Deep Research",
            published_at=datetime.now(UTC),
            content_hash="a" * 64,
            category="deep_research",
        )
        article.mentions = []
        article.sentiment_analyses = [
            SentimentAnalysis(
                id=uuid.uuid4(),
                article_id=article_id,
                sentiment_score=0.45,
                confidence=0.82,
                impact_timeline="short_term",
                analyzed_at=datetime.now(UTC),
            )
        ]
        mock_db.execute = AsyncMock(return_value=_ScalarRows([article]))

        with patch(
            "app.api.v1.research.ResearchService.get_task_result",
            return_value={
                "task_id": "task-2",
                "status": "SUCCESS",
                "result": {
                    "user_id": "00000000-0000-4000-8000-000000000001",
                    "topic": "inflation",
                    "new_articles": 1,
                    "total_found": 5,
                    "article_ids": [str(article_id)],
                    "query_count": 3,
                },
            },
        ):
            resp = await client.get("/api/v1/research/result/task-2")

        assert resp.status_code == 200
        payload = resp.json()
        assert payload["sentiment"]["overall_label"] == "bullish"
        assert payload["sentiment"]["analyzed_articles"] == 1
        assert payload["new_articles"] == 1
        assert len(payload["articles"]) == 1

    async def test_result_in_progress_returns_conflict(self, client):
        with patch(
            "app.api.v1.research.ResearchService.get_task_result",
            return_value={"task_id": "task-3", "status": "PROGRESS", "result": None},
        ):
            resp = await client.get("/api/v1/research/result/task-3")

        assert resp.status_code == 409

    async def test_result_forbidden_for_other_user(self, client):
        with patch(
            "app.api.v1.research.ResearchService.get_task_result",
            return_value={
                "task_id": "task-4",
                "status": "SUCCESS",
                "result": {
                    "user_id": "11111111-0000-4000-8000-000000000000",
                    "new_articles": 0,
                    "total_found": 0,
                    "article_ids": [],
                },
            },
        ):
            resp = await client.get("/api/v1/research/result/task-4")

        assert resp.status_code == 403
