"""Firecrawl client wrapper for web search and scraping."""

import logging
from urllib.parse import urlparse

from pipeline.config import settings

logger = logging.getLogger(__name__)

# Indian financial news domains used to bias search results.
INDIAN_FINANCIAL_SOURCES = [
    "moneycontrol.com",
    "economictimes.indiatimes.com",
    "livemint.com",
    "business-standard.com",
    "ndtvprofit.com",
    "financialexpress.com",
    "zeebiz.com",
    "bloombergquint.com",
    "reuters.com",
    "thehindu.com",
]


class FirecrawlClient:
    """Wrapper around the Firecrawl Python SDK for web search and scraping."""

    def __init__(self) -> None:
        """Initialize the Firecrawl client.

        Lazily initializes the SDK so import-time failures are avoided when
        the API key is not yet configured.
        """
        self._app = None

    def _get_app(self):
        """Lazily initialize the Firecrawl SDK instance."""
        if self._app is None:
            if not settings.FIRECRAWL_API_KEY:
                logger.warning(
                    "Firecrawl API key not configured. Set FIRECRAWL_API_KEY "
                    "in environment or .env file."
                )
                return None
            from firecrawl import Firecrawl

            self._app = Firecrawl(api_key=settings.FIRECRAWL_API_KEY)
            logger.info("Firecrawl client initialized successfully")
        return self._app

    @staticmethod
    def _extract_source_name(url: str) -> str:
        """Extract a human-readable source name from a URL."""
        try:
            hostname = urlparse(url).hostname or ""
            # Strip common prefixes
            for prefix in ("www.", "m.", "amp."):
                if hostname.startswith(prefix):
                    hostname = hostname[len(prefix) :]
            return hostname
        except Exception:
            return ""

    def search_news(self, query: str, limit: int = 10) -> list[dict]:
        """Search for news articles using the Firecrawl /v2/search endpoint.

        Args:
            query: Search query string.
            limit: Maximum number of results to return.

        Returns:
            List of normalized article dicts.
        """
        logger.info("Firecrawl search: %s (limit=%d)", query, limit)
        try:
            app = self._get_app()
            if app is None:
                return []

            response = app.search(query, limit=limit)

            # The SDK may return a list directly or a dict with a "data" key
            # depending on the version. Handle both.
            if isinstance(response, dict):
                results = response.get("data", [])
            elif isinstance(response, list):
                results = response
            else:
                results = []

            articles: list[dict] = []
            for item in results:
                # Handle both object-attribute and dict access patterns
                if hasattr(item, "get"):
                    raw = item
                elif hasattr(item, "__dict__"):
                    raw = vars(item)
                else:
                    raw = {}

                url = raw.get("url", "")
                articles.append(
                    {
                        "title": raw.get("title", ""),
                        "url": url,
                        "content": raw.get("markdown", raw.get("content", "")),
                        "source_name": self._extract_source_name(url),
                        "published_at": raw.get("published_at", None),
                        "scraper_source": "firecrawl",
                    }
                )

            logger.info(
                "Firecrawl search returned %d results for: %s",
                len(articles),
                query,
            )
            return articles
        except Exception as e:
            logger.error("Firecrawl search error for '%s': %s", query, str(e))
            return []

    def scrape_url(self, url: str) -> dict | None:
        """Scrape a single URL using the Firecrawl /v2/scrape endpoint.

        Args:
            url: The URL to scrape.

        Returns:
            Normalized article dict or None on failure.
        """
        logger.info("Firecrawl scrape: %s", url)
        try:
            app = self._get_app()
            if app is None:
                return None

            response = app.scrape(url)

            if isinstance(response, dict):
                raw = response
            elif hasattr(response, "__dict__"):
                raw = vars(response)
            else:
                raw = {}

            # The scrape response usually nests data under a "data" key.
            data = raw.get("data", raw) if isinstance(raw, dict) else raw

            return {
                "title": data.get("title", data.get("metadata", {}).get("title", "")),
                "url": url,
                "content": data.get("markdown", data.get("content", "")),
                "source_name": self._extract_source_name(url),
                "published_at": None,
                "scraper_source": "firecrawl",
            }
        except Exception as e:
            logger.error("Firecrawl scrape error for '%s': %s", url, str(e))
            return None

    def search_indian_financial_news(self, query: str, limit: int = 10) -> list[dict]:
        """Search for Indian financial news.

        Augments the query with India-specific context and financial source
        hints to bias results towards Indian financial news outlets.

        Args:
            query: Base search query.
            limit: Maximum number of results to return.

        Returns:
            List of normalized article dicts.
        """
        augmented_query = f"{query} India finance"
        logger.info(
            "Firecrawl Indian financial news search: %s (limit=%d)",
            augmented_query,
            limit,
        )

        # Fetch more than requested so we can prioritise Indian sources.
        raw_results = self.search_news(augmented_query, limit=limit * 2)

        # Separate into Indian-source and other results.
        indian: list[dict] = []
        other: list[dict] = []
        for article in raw_results:
            source = article.get("source_name", "")
            if any(domain in source for domain in INDIAN_FINANCIAL_SOURCES):
                indian.append(article)
            else:
                other.append(article)

        # Prefer Indian sources, backfill with others up to limit.
        results = (indian + other)[:limit]
        logger.info(
            "Indian financial news: %d Indian-source, %d other (returning %d)",
            len(indian),
            len(other),
            len(results),
        )
        return results
