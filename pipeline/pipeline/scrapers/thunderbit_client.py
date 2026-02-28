"""Thunderbit client wrapper for AI-powered web scraping."""

import logging
from urllib.parse import urlparse

import httpx

from pipeline.config import settings

logger = logging.getLogger(__name__)

THUNDERBIT_BASE_URL = "https://api.thunderbit.com/v1"


class ThunderbitClient:
    """Wrapper around the Thunderbit API for AI-powered scraping."""

    def __init__(self) -> None:
        """Initialize the Thunderbit client."""
        self._api_key = settings.THUNDERBIT_API_KEY
        if not self._api_key:
            logger.warning(
                "Thunderbit API key not configured. Set THUNDERBIT_API_KEY "
                "in environment or .env file."
            )

    def _headers(self) -> dict[str, str]:
        """Return authorization headers for the Thunderbit API."""
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _extract_source_name(url: str) -> str:
        """Extract a human-readable source name from a URL."""
        try:
            hostname = urlparse(url).hostname or ""
            for prefix in ("www.", "m.", "amp."):
                if hostname.startswith(prefix):
                    hostname = hostname[len(prefix) :]
            return hostname
        except Exception:
            return ""

    def scrape_url(self, url: str) -> dict | None:
        """Scrape a single URL using the Thunderbit API.

        Args:
            url: The URL to scrape.

        Returns:
            Normalized article dict, or None on failure.
        """
        logger.info("Thunderbit scrape: %s", url)
        if not self._api_key:
            logger.warning("Thunderbit API key not configured, cannot scrape.")
            return None

        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    f"{THUNDERBIT_BASE_URL}/scrape",
                    headers=self._headers(),
                    json={"url": url},
                )
                if response.status_code != 200:
                    logger.error(
                        "Thunderbit scrape error: %s - %s",
                        response.status_code,
                        response.text,
                    )
                    return None

                data = response.json()

            result = data.get("data", data)
            return {
                "title": result.get("title", ""),
                "url": url,
                "content": result.get("markdown", result.get("content", "")),
                "source_name": self._extract_source_name(url),
                "published_at": result.get("published_at", None),
                "scraper_source": "thunderbit",
            }
        except Exception as e:
            logger.error("Thunderbit scrape error for '%s': %s", url, str(e))
            return None

    def extract_articles(self, urls: list[str]) -> list[dict]:
        """Batch scrape multiple URLs.

        Args:
            urls: List of URLs to scrape.

        Returns:
            List of normalized article dicts (failed URLs are skipped).
        """
        logger.info("Thunderbit batch extract: %d URLs", len(urls))
        articles: list[dict] = []
        for url in urls:
            try:
                result = self.scrape_url(url)
                if result is not None:
                    articles.append(result)
            except Exception as e:
                logger.error("Thunderbit batch extract error for '%s': %s", url, str(e))
        logger.info(
            "Thunderbit batch extract completed: %d/%d succeeded",
            len(articles),
            len(urls),
        )
        return articles

    def search_and_scrape(self, query: str, limit: int = 10) -> list[dict]:
        """Search for content and scrape matching pages.

        Uses the Thunderbit search endpoint if available. Falls back to
        returning an empty list if the endpoint is not supported.

        Args:
            query: Search query string.
            limit: Maximum number of results.

        Returns:
            List of normalized article dicts.
        """
        logger.info("Thunderbit search_and_scrape: %s (limit=%d)", query, limit)
        if not self._api_key:
            logger.warning("Thunderbit API key not configured, cannot search.")
            return []

        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    f"{THUNDERBIT_BASE_URL}/search",
                    headers=self._headers(),
                    json={"query": query, "limit": limit},
                )
                if response.status_code != 200:
                    logger.warning(
                        "Thunderbit search endpoint returned %s - "
                        "endpoint may not be available: %s",
                        response.status_code,
                        response.text,
                    )
                    return []

                data = response.json()

            raw_results = data.get("data", data.get("results", []))
            if not isinstance(raw_results, list):
                raw_results = []

            articles: list[dict] = []
            for item in raw_results:
                url = item.get("url", "")
                articles.append(
                    {
                        "title": item.get("title", ""),
                        "url": url,
                        "content": item.get("markdown", item.get("content", "")),
                        "source_name": self._extract_source_name(url),
                        "published_at": item.get("published_at", None),
                        "scraper_source": "thunderbit",
                    }
                )

            logger.info(
                "Thunderbit search returned %d results for: %s",
                len(articles),
                query,
            )
            return articles[:limit]
        except Exception as e:
            logger.error(
                "Thunderbit search_and_scrape error for '%s': %s", query, str(e)
            )
            return []
