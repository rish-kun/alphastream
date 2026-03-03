"""Service for dispatching extensive research tasks to the pipeline."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from celery import Celery
from app.config import settings

logger = logging.getLogger(__name__)

# Create a Celery client that connects to the same broker as the pipeline
_celery_app = Celery(
    "alphastream",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)
_celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
)


class ResearchService:
    @staticmethod
    def _parse_datetime(value: object) -> datetime | None:
        if not isinstance(value, str):
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None

    @staticmethod
    def _derive_progress_metrics(progress: dict) -> dict:
        enriched = dict(progress)
        total_queries = enriched.get("total_queries")
        completed_queries = enriched.get("completed_queries")
        started_at = ResearchService._parse_datetime(enriched.get("started_at"))

        if isinstance(total_queries, int) and total_queries > 0:
            if isinstance(completed_queries, int):
                pct = (completed_queries / total_queries) * 100
                enriched["percent_complete"] = round(max(0.0, min(100.0, pct)), 2)

        elapsed_seconds: int | None = None
        if started_at is not None:
            elapsed = datetime.now(UTC) - started_at.astimezone(UTC)
            elapsed_seconds = max(0, int(elapsed.total_seconds()))
            enriched["elapsed_seconds"] = elapsed_seconds

        eta_seconds: int | None = None
        if (
            elapsed_seconds is not None
            and isinstance(total_queries, int)
            and isinstance(completed_queries, int)
            and total_queries > 0
            and completed_queries > 0
            and completed_queries < total_queries
        ):
            avg_per_query = elapsed_seconds / completed_queries
            eta_seconds = int(avg_per_query * (total_queries - completed_queries))
        enriched["eta_seconds"] = eta_seconds

        low: int | None = None
        high: int | None = None
        articles_new = enriched.get("articles_new_so_far")
        if (
            isinstance(articles_new, int)
            and isinstance(total_queries, int)
            and isinstance(completed_queries, int)
            and total_queries > 0
            and completed_queries > 0
        ):
            projected = (articles_new / completed_queries) * total_queries
            spread = max(3.0, projected * 0.35)
            low = max(0, int(round(projected - spread)))
            high = max(low, int(round(projected + spread)))
        elif isinstance(articles_new, int):
            low = max(0, articles_new)
            high = max(low, articles_new + 3)

        enriched["expected_new_articles_low"] = low
        enriched["expected_new_articles_high"] = high

        return enriched

    @staticmethod
    def research_stock(ticker: str, user_id: str) -> str:
        """Dispatch extensive research for a single stock. Returns Celery task ID."""
        result = _celery_app.send_task(
            "pipeline.tasks.extensive_research.research_stock",
            args=[ticker, user_id],
        )
        logger.info("Dispatched stock research for %s, task_id=%s", ticker, result.id)
        return result.id

    @staticmethod
    def research_topic(topic: str, user_id: str) -> str:
        """Dispatch extensive research for a topic. Returns Celery task ID."""
        result = _celery_app.send_task(
            "pipeline.tasks.extensive_research.research_topic",
            args=[topic, user_id],
        )
        logger.info("Dispatched topic research for '%s', task_id=%s", topic, result.id)
        return result.id

    @staticmethod
    def research_portfolio(portfolio_id: str, user_id: str) -> str:
        """Dispatch extensive research for all stocks in a portfolio. Returns Celery task ID."""
        result = _celery_app.send_task(
            "pipeline.tasks.extensive_research.research_portfolio",
            args=[portfolio_id, user_id],
        )
        logger.info(
            "Dispatched portfolio research for %s, task_id=%s", portfolio_id, result.id
        )
        return result.id

    @staticmethod
    def get_task_status(task_id: str) -> dict:
        """Check status of a research task. Returns dict with state and info."""
        result = _celery_app.AsyncResult(task_id)
        response = {"task_id": task_id, "status": result.state}
        if result.state == "PROGRESS":
            progress = result.info if isinstance(result.info, dict) else {}
            response["progress"] = ResearchService._derive_progress_metrics(progress)
        elif result.state == "SUCCESS":
            response["result"] = result.result
        elif result.state == "FAILURE":
            response["error"] = str(result.result) if result.result else "Unknown error"
        return response

    @staticmethod
    def get_task_result(task_id: str) -> dict:
        result = _celery_app.AsyncResult(task_id)
        return {
            "task_id": task_id,
            "status": result.state,
            "result": result.result if isinstance(result.result, dict) else None,
            "info": result.info if isinstance(result.info, dict) else None,
        }
