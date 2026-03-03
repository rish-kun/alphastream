"""Tests for sentiment API endpoints."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from app.tests.conftest import MockResult


class TestSentimentOverview:
    async def test_returns_overview(self, client: AsyncClient, mock_db: AsyncMock):
        # Mock the sequence of DB calls in the sentiment overview endpoint:
        # 1. avg sentiment -> 0.35
        # 2. bullish count -> 10
        # 3. bearish count -> 5
        # 4. neutral count -> 15
        # 5. top movers -> empty list
        mock_db.execute.side_effect = [
            MockResult(scalar=0.35),  # avg sentiment
            MockResult(scalar=10),  # bullish
            MockResult(scalar=5),  # bearish
            MockResult(scalar=15),  # neutral
            MockResult(data=[]),  # top movers
        ]

        resp = await client.get("/api/v1/sentiment/overview")

        assert resp.status_code == 200
        data = resp.json()
        assert data["market_sentiment"] == 0.35
        assert data["bullish_count"] == 10
        assert data["bearish_count"] == 5
        assert data["neutral_count"] == 15
        assert data["top_movers"] == []

    async def test_overview_with_null_sentiment(
        self, client: AsyncClient, mock_db: AsyncMock
    ):
        # When no analyses exist, avg returns None -> should default to 0.0
        mock_db.execute.side_effect = [
            MockResult(scalar=None),  # avg sentiment (no data)
            MockResult(scalar=0),  # bullish
            MockResult(scalar=0),  # bearish
            MockResult(scalar=0),  # neutral
            MockResult(data=[]),  # top movers
        ]

        resp = await client.get("/api/v1/sentiment/overview")

        assert resp.status_code == 200
        data = resp.json()
        assert data["market_sentiment"] == 0.0
        assert data["bullish_count"] == 0


class TestSectorSentiment:
    async def test_returns_sectors(self, client: AsyncClient, mock_db: AsyncMock):
        # Mock: main sector query returns no rows -> empty list
        mock_db.execute.return_value = MockResult(data=[])

        resp = await client.get("/api/v1/sentiment/sectors")

        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 0

    async def test_sectors_with_data(self, client: AsyncClient, mock_db: AsyncMock):
        # Mock sector rows: (sector_name, avg_sentiment, article_count)
        sector_row = ("Banking & Finance", 0.45, 25)

        # First call: sector query returns one row
        # Second call: top stocks query for that sector
        mock_db.execute.side_effect = [
            MockResult(data=[sector_row]),  # sector query
            MockResult(data=[("HDFCBANK",), ("ICICIBANK",)]),  # top stocks
        ]

        resp = await client.get("/api/v1/sentiment/sectors")

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["sector"] == "Banking & Finance"
        assert data[0]["sentiment_score"] == 0.45
        assert data[0]["article_count"] == 25
        assert "HDFCBANK" in data[0]["top_stocks"]


class TestSentimentReanalysis:
    async def test_reanalyze_dispatches_existing_articles(
        self, client: AsyncClient, mock_db: AsyncMock
    ):
        article_id = uuid.uuid4()
        mock_db.execute.return_value = MockResult(data=[article_id])

        with patch("app.api.v1.sentiment._celery_app.send_task") as mock_send_task:
            mock_send_task.return_value = MagicMock(id="task-123")

            resp = await client.post(
                "/api/v1/sentiment/reanalyze",
                json={"article_ids": [str(article_id)],
                      "force_reanalyze": True},
            )

        assert resp.status_code == 202
        data = resp.json()
        assert data["dispatched"] == 1
        assert data["task_ids"] == ["task-123"]
        assert data["skipped_article_ids"] == []

    async def test_reanalyze_skips_missing_articles(
        self, client: AsyncClient, mock_db: AsyncMock
    ):
        article_id = uuid.uuid4()
        mock_db.execute.return_value = MockResult(data=[])

        with patch("app.api.v1.sentiment._celery_app.send_task") as mock_send_task:
            resp = await client.post(
                "/api/v1/sentiment/reanalyze",
                json={"article_ids": [str(article_id)],
                      "force_reanalyze": True},
            )

        assert resp.status_code == 202
        data = resp.json()
        assert data["dispatched"] == 0
        assert data["task_ids"] == []
        assert data["skipped_article_ids"] == [str(article_id)]
        mock_send_task.assert_not_called()

    async def test_reanalyze_all_dispatches_job(self, client: AsyncClient):
        with patch("app.api.v1.sentiment._celery_app.send_task") as mock_send_task:
            mock_send_task.return_value = MagicMock(id="bulk-task-1")

            resp = await client.post(
                "/api/v1/sentiment/reanalyze-all",
                json={"force_reanalyze": True, "batch_size": 25},
            )

        assert resp.status_code == 202
        data = resp.json()
        assert data["task_id"] == "bulk-task-1"
        assert data["status"] == "dispatched"

    async def test_reanalyze_all_status_progress(self, client: AsyncClient):
        mock_result = MagicMock()
        mock_result.state = "PROGRESS"
        mock_result.info = {"dispatched": 20, "targeted_articles": 100}

        with patch("app.api.v1.sentiment._celery_app.AsyncResult") as mock_async_result:
            mock_async_result.return_value = mock_result
            resp = await client.get("/api/v1/sentiment/reanalyze-all/status/job-1")

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "PROGRESS"
        assert data["progress"]["dispatched"] == 20

    async def test_reanalyze_all_status_failure(self, client: AsyncClient):
        mock_result = MagicMock()
        mock_result.state = "FAILURE"
        mock_result.info = RuntimeError("boom")

        with patch("app.api.v1.sentiment._celery_app.AsyncResult") as mock_async_result:
            mock_async_result.return_value = mock_result
            resp = await client.get("/api/v1/sentiment/reanalyze-all/status/job-2")

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "FAILURE"
        assert "boom" in data["error"]
