"""Browse.ai client wrapper for robot-based web scraping."""

import logging
import time

import httpx

from pipeline.config import settings

logger = logging.getLogger(__name__)

BROWSEAI_BASE_URL = "https://api.browse.ai/v2"


class BrowseAIClient:
    """Wrapper around the Browse.ai REST API v2 for robot-based scraping."""

    def __init__(self) -> None:
        """Initialize the Browse.ai client."""
        self._api_key = settings.BROWSEAI_API_KEY
        self._default_robot_id = settings.BROWSEAI_DEFAULT_ROBOT_ID
        if not self._api_key:
            logger.warning(
                "Browse.ai API key not configured. Set BROWSEAI_API_KEY "
                "in environment or .env file."
            )

    def _headers(self) -> dict[str, str]:
        """Return authorization headers for the Browse.ai API."""
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    def trigger_robot(self, robot_id: str, input_params: dict) -> str | None:
        """Trigger a Browse.ai robot run.

        Args:
            robot_id: The robot ID to trigger.
            input_params: Input parameters for the robot.

        Returns:
            The task ID of the triggered run, or None on failure.
        """
        logger.info("Triggering Browse.ai robot %s", robot_id)
        if not self._api_key:
            logger.warning("Browse.ai API key not configured, cannot trigger robot.")
            return None

        try:
            url = f"{BROWSEAI_BASE_URL}/robots/{robot_id}/tasks"
            payload = {"inputParameters": input_params}
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, headers=self._headers(), json=payload)
                if response.status_code not in (200, 201):
                    logger.error(
                        "Browse.ai trigger error: %s - %s",
                        response.status_code,
                        response.text,
                    )
                    return None

                data = response.json()
            task_id = (
                data.get("result", {}).get("id") or data.get("statusCode")  # fallback
            )
            logger.info("Browse.ai robot %s triggered, task_id=%s", robot_id, task_id)
            return task_id
        except Exception as e:
            logger.error("Browse.ai trigger error for robot %s: %s", robot_id, str(e))
            return None

    def get_task_result(self, robot_id: str, task_id: str) -> dict | None:
        """Fetch the result of a Browse.ai task.

        Args:
            robot_id: The robot ID.
            task_id: The task ID to query.

        Returns:
            The task result dict, or None if not yet complete / on failure.
        """
        logger.debug("Polling Browse.ai task %s for robot %s", task_id, robot_id)
        if not self._api_key:
            return None

        try:
            url = f"{BROWSEAI_BASE_URL}/robots/{robot_id}/tasks/{task_id}"
            with httpx.Client(timeout=30.0) as client:
                response = client.get(url, headers=self._headers())
                if response.status_code != 200:
                    logger.error(
                        "Browse.ai task poll error: %s - %s",
                        response.status_code,
                        response.text,
                    )
                    return None

                data = response.json()
            result = data.get("result", {})
            status = result.get("status", "")

            if status == "successful":
                return result
            if status in ("failed", "cancelled"):
                logger.warning(
                    "Browse.ai task %s finished with status: %s", task_id, status
                )
                return None

            # Still running
            return None
        except Exception as e:
            logger.error(
                "Browse.ai task poll error for %s/%s: %s", robot_id, task_id, str(e)
            )
            return None

    def run_and_wait(
        self,
        robot_id: str,
        input_params: dict,
        timeout: int = 120,
        poll_interval: int = 5,
    ) -> dict | None:
        """Trigger a robot run and poll until completion or timeout.

        Args:
            robot_id: The robot ID to run.
            input_params: Input parameters for the robot.
            timeout: Maximum seconds to wait for the task to complete.
            poll_interval: Seconds between poll attempts.

        Returns:
            The task result dict, or None on failure/timeout.
        """
        task_id = self.trigger_robot(robot_id, input_params)
        if task_id is None:
            return None

        logger.info("Waiting for Browse.ai task %s (timeout=%ds)", task_id, timeout)
        elapsed = 0
        while elapsed < timeout:
            time.sleep(poll_interval)
            elapsed += poll_interval
            result = self.get_task_result(robot_id, task_id)
            if result is not None:
                logger.info("Browse.ai task %s completed", task_id)
                return result

        logger.warning("Browse.ai task %s timed out after %ds", task_id, timeout)
        return None

    def search_financial_news(
        self, query: str, robot_id: str | None = None
    ) -> list[dict]:
        """Search financial news using a configured Browse.ai robot.

        Args:
            query: Search query string.
            robot_id: Robot ID to use. Defaults to the configured default.

        Returns:
            List of normalized article dicts.
        """
        rid = robot_id or self._default_robot_id
        if not rid:
            logger.warning(
                "No robot ID provided and BROWSEAI_DEFAULT_ROBOT_ID not configured."
            )
            return []

        logger.info("Browse.ai financial news search: %s (robot=%s)", query, rid)
        try:
            result = self.run_and_wait(rid, {"search_query": query})
            if result is None:
                return []

            # Browse.ai returns captured data under various keys depending on
            # the robot configuration. We normalise the most common shapes.
            captured = result.get("capturedLists", {})

            # Try to find the first non-empty list of items.
            items: list[dict] = []
            if captured:
                for _key, rows in captured.items():
                    if isinstance(rows, list) and rows:
                        items = rows
                        break

            # If no captured lists, fall back to capturedTexts.
            if not items:
                texts = result.get("capturedTexts", {})
                if texts:
                    items = [texts]

            articles: list[dict] = []
            for item in items:
                articles.append(
                    {
                        "title": item.get("title", item.get("headline", "")),
                        "url": item.get("url", item.get("link", "")),
                        "content": item.get("content", item.get("description", "")),
                        "source_name": item.get("source", item.get("source_name", "")),
                        "published_at": item.get(
                            "published_at", item.get("date", None)
                        ),
                        "scraper_source": "browseai",
                    }
                )

            logger.info(
                "Browse.ai financial news returned %d results for: %s",
                len(articles),
                query,
            )
            return articles
        except Exception as e:
            logger.error(
                "Browse.ai financial news search error for '%s': %s", query, str(e)
            )
            return []
