"""Service for tracking article reanalysis status in Redis."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from redis.asyncio import Redis

from app.config import settings

logger = logging.getLogger(__name__)

REDIS_KEY_PREFIX = "reanalysis:article"
REDIS_TTL_SECONDS = 300  # 5 minutes


class ReanalysisStatus(str, Enum):
    """Status values for article reanalysis."""

    PENDING = "pending"
    STARTED = "started"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"


class ReanalysisStatusService:
    """Manages reanalysis status tracking using Redis."""

    def __init__(self) -> None:
        self._redis: Redis | None = None

    async def _get_redis(self) -> Redis:
        """Get or create Redis connection."""
        if self._redis is None:
            self._redis = Redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
            )
        return self._redis

    def _make_key(self, article_id: str) -> str:
        """Create Redis key for article reanalysis status."""
        return f"{REDIS_KEY_PREFIX}:{article_id}"

    async def start_reanalysis(
        self,
        article_id: str,
        task_id: str,
        user_id: str | None = None,
    ) -> None:
        """Mark reanalysis as started for an article."""
        redis = await self._get_redis()
        key = self._make_key(article_id)

        data = {
            "article_id": article_id,
            "task_id": task_id,
            "status": ReanalysisStatus.STARTED,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id,
            "progress": None,
            "error": None,
        }

        await redis.setex(key, REDIS_TTL_SECONDS, json.dumps(data))
        logger.debug("Started tracking reanalysis for article %s", article_id)

    async def update_progress(
        self,
        article_id: str,
        progress: dict[str, Any],
    ) -> None:
        """Update reanalysis progress for an article."""
        redis = await self._get_redis()
        key = self._make_key(article_id)

        existing = await redis.get(key)
        if not existing:
            logger.warning("No existing reanalysis status for article %s", article_id)
            return

        data = json.loads(existing)
        data["status"] = ReanalysisStatus.ANALYZING
        data["progress"] = progress
        data["updated_at"] = datetime.now(timezone.utc).isoformat()

        await redis.setex(key, REDIS_TTL_SECONDS, json.dumps(data))

    async def complete_reanalysis(
        self,
        article_id: str,
        result: dict[str, Any] | None = None,
    ) -> None:
        """Mark reanalysis as completed for an article."""
        redis = await self._get_redis()
        key = self._make_key(article_id)

        existing = await redis.get(key)
        if not existing:
            logger.debug("No tracking entry for completed article %s", article_id)
            return

        data = json.loads(existing)
        data["status"] = ReanalysisStatus.COMPLETED
        data["completed_at"] = datetime.now(timezone.utc).isoformat()
        data["result"] = result

        await redis.setex(key, 60, json.dumps(data))
        logger.debug("Completed reanalysis for article %s", article_id)

    async def fail_reanalysis(
        self,
        article_id: str,
        error: str,
    ) -> None:
        """Mark reanalysis as failed for an article."""
        redis = await self._get_redis()
        key = self._make_key(article_id)

        existing = await redis.get(key)
        if not existing:
            logger.debug("No tracking entry for failed article %s", article_id)
            return

        data = json.loads(existing)
        data["status"] = ReanalysisStatus.FAILED
        data["failed_at"] = datetime.now(timezone.utc).isoformat()
        data["error"] = error

        await redis.setex(key, 60, json.dumps(data))
        logger.debug("Failed reanalysis for article %s: %s", article_id, error)

    async def get_status(self, article_id: str) -> dict[str, Any] | None:
        """Get current reanalysis status for an article."""
        redis = await self._get_redis()
        key = self._make_key(article_id)

        data = await redis.get(key)
        if not data:
            return None

        return json.loads(data)

    async def is_reanalyzing(self, article_id: str) -> bool:
        """Check if article is currently being reanalyzed."""
        status = await self.get_status(article_id)
        if not status:
            return False

        return status["status"] in (
            ReanalysisStatus.PENDING,
            ReanalysisStatus.STARTED,
            ReanalysisStatus.ANALYZING,
        )

    async def cleanup(self) -> None:
        """Clean up Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None


# Global instance
reanalysis_status_service = ReanalysisStatusService()
