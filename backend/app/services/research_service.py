"""Service for dispatching extensive research tasks to the pipeline."""

from __future__ import annotations

import logging
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
            response["progress"] = result.info
        elif result.state == "SUCCESS":
            response["result"] = result.result
        elif result.state == "FAILURE":
            response["error"] = str(result.result) if result.result else "Unknown error"
        return response
