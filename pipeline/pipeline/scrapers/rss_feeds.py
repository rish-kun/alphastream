"""RSS feed parser for Indian financial news sources."""

import logging
from datetime import datetime

import feedparser

from pipeline.config import settings

logger = logging.getLogger(__name__)


class RSSFeedParser:
    """Parses RSS feeds and extracts article metadata."""

    def fetch_feed(self, url: str, timeout: int | None = None) -> list[dict]:
        """Fetch and parse an RSS feed.

        Args:
            url: URL of the RSS feed.
            timeout: Request timeout in seconds. Defaults to config value.

        Returns:
            List of parsed feed entry dicts.
        """
        timeout = timeout or settings.RSS_FETCH_TIMEOUT
        logger.info("Fetching RSS feed: %s (timeout=%ds)", url, timeout)
        feed = feedparser.parse(url)
        if feed.bozo:
            logger.warning("Feed parse warning for %s: %s", url, feed.bozo_exception)
        return [
            self.parse_entry(entry)
            for entry in feed.entries[: settings.MAX_ARTICLES_PER_FEED]
        ]

    def parse_entry(self, entry) -> dict:
        """Parse a single feed entry into a standardized dict.

        Args:
            entry: A feedparser entry object.

        Returns:
            Dict with keys: title, summary, link, published, source.
        """
        published = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            published = datetime(*entry.published_parsed[:6]).isoformat()

        return {
            "title": getattr(entry, "title", ""),
            "summary": getattr(entry, "summary", ""),
            "link": getattr(entry, "link", ""),
            "published": published,
            "source": getattr(entry, "source", {}).get("title", ""),
        }

    def deduplicate(self, entries: list[dict]) -> list[dict]:
        """Remove duplicate entries based on link URL.

        Args:
            entries: List of parsed feed entry dicts.

        Returns:
            Deduplicated list of entries.
        """
        seen_links: set[str] = set()
        unique: list[dict] = []
        for entry in entries:
            link = entry.get("link", "")
            if link and link not in seen_links:
                seen_links.add(link)
                unique.append(entry)
        return unique
