"""Google News scraper client for financial news aggregation."""

import logging
import random
import re
import time
from datetime import datetime, timedelta
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from pipeline.config import settings

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

GOOGLE_NEWS_BASE_URL = "https://news.google.com"
GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/search"


class GoogleNewsClient:
    """Scraper for Google News search results using RSS feed."""

    def __init__(
        self,
        proxy: str | None = None,
        max_retries: int = 3,
        timeout: int = 30,
    ) -> None:
        """Initialize the Google News client.

        Args:
            proxy: Optional proxy URL for requests.
            max_retries: Maximum number of retry attempts for failed requests.
            timeout: Request timeout in seconds.
        """
        self._session = None
        self._proxy = proxy
        self._max_retries = max_retries
        self._timeout = timeout

    def _get_session(self) -> requests.Session:
        """Lazily initialize the requests session."""
        if self._session is None:
            self._session = requests.Session()
            if self._proxy:
                self._session.proxies = {"http": self._proxy, "https": self._proxy}
        return self._session

    def _headers(self) -> dict[str, str]:
        """Return headers for requests with rotating User-Agent."""
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "application/rss+xml, application/xml, text/xml, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }

    def _make_request(self, url: str) -> requests.Response | None:
        """Make a request with retry logic and exponential backoff.

        Args:
            url: The URL to fetch.

        Returns:
            Response object or None on failure.
        """
        session = self._get_session()
        for attempt in range(self._max_retries):
            try:
                response = session.get(
                    url,
                    headers=self._headers(),
                    timeout=self._timeout,
                    allow_redirects=True,
                )
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                wait_time = 2**attempt + random.uniform(0, 1)
                logger.warning(
                    "Request failed (attempt %d/%d) for %s: %s. Retrying in %.2fs...",
                    attempt + 1,
                    self._max_retries,
                    url,
                    str(e),
                    wait_time,
                )
                if attempt < self._max_retries - 1:
                    time.sleep(wait_time)
        logger.error("All retry attempts failed for URL: %s", url)
        return None

    def search(self, query: str, max_results: int = 20) -> list[dict]:
        """Search Google News for articles matching the query.

        Args:
            query: Search query string.
            max_results: Maximum number of articles to return.

        Returns:
            List of normalized article dicts.
        """
        logger.info("Google News search: %s (max_results=%d)", query, max_results)

        encoded_query = requests.utils.quote(query)
        url = f"{GOOGLE_NEWS_RSS_URL}?q={encoded_query}&hl=en-US&gl=US"

        response = self._make_request(url)
        if response is None:
            return []

        articles = self._parse_rss(response.text, max_results)

        logger.info(
            "Google News search returned %d results for: %s",
            len(articles),
            query,
        )
        return articles

    def _parse_rss(self, xml: str, max_results: int) -> list[dict]:
        """Parse Google News RSS feed.

        Args:
            xml: Raw XML response from RSS feed.
            max_results: Maximum number of articles to return.

        Returns:
            List of normalized article dicts.
        """
        soup = BeautifulSoup(xml, "xml")
        articles: list[dict] = []

        items = soup.find_all("item")

        for item in items:
            if len(articles) >= max_results:
                break

            article = self._parse_rss_item(item)
            if article:
                articles.append(article)

        return articles

    def _parse_rss_item(self, item: BeautifulSoup) -> dict | None:
        """Parse individual RSS item element.

        Args:
            item: BeautifulSoup element representing an RSS item.

        Returns:
            Normalized article dict or None if parsing fails.
        """
        try:
            title_elem = item.find("title")
            title = title_elem.get_text(strip=True) if title_elem else ""

            if not title:
                return None

            url = ""
            link_elem = item.find("link")
            if link_elem:
                link = link_elem.get_text(strip=True)
                if link:
                    url = self._extract_article_url(link)

            if not url:
                return None

            source_elem = item.find("source")
            source_name = ""
            source_url_attr = ""
            if source_elem:
                source_name = source_elem.get_text(strip=True)
                source_url_attr = source_elem.get("url", "")

            if not source_name:
                try:
                    parsed = urlparse(url)
                    source_name = parsed.netloc.replace("www.", "")
                except Exception:
                    source_name = ""

            pub_date_elem = item.find("pubDate")
            published_at = None
            if pub_date_elem:
                pub_date = pub_date_elem.get_text(strip=True)
                if pub_date:
                    published_at = self._parse_rss_time(pub_date)

            description_elem = item.find("description")
            content = ""
            if description_elem:
                raw_desc = description_elem.get_text(strip=True)
                content = self._strip_html(raw_desc)

            if source_url_attr and source_url_attr.startswith("http"):
                url = source_url_attr

            return {
                "title": title,
                "url": url,
                "content": content,
                "source_name": source_name,
                "published_at": published_at,
                "scraper_source": "google_news",
            }

        except Exception as e:
            logger.debug("Failed to parse RSS item: %s", str(e))
            return None

    def _extract_article_url(self, link: str) -> str:
        """Extract direct article URL from Google News redirect URL.

        Args:
            link: Google News RSS link URL.

        Returns:
            Direct article URL.
        """
        if not link:
            return ""

        if "/articles/" in link:
            match = re.search(r"/articles/([A-Za-z0-9_-]+)", link)
            if match:
                article_id = match.group(1)
                try:
                    decoded = self._decode_google_article_id(article_id)
                    if decoded:
                        return decoded
                except Exception:
                    pass

        if link.startswith("http") and "news.google.com" not in link:
            return link

        return link

    def _decode_google_article_id(self, article_id: str) -> str | None:
        """Decode Google News article ID to extract original URL.

        Args:
            article_id: Google News article ID (e.g., CBMivAFB...).

        Returns:
            Decoded article URL or None if decoding fails.
        """
        import base64

        try:
            encoded = article_id
            padded = encoded + "=" * (4 - len(encoded) % 4)
            decoded = base64.urlsafe_b64decode(padded).decode("utf-16", errors="ignore")
            url_match = re.search(r"https?://[^\x00-\x1f]+", decoded)
            if url_match:
                return url_match.group(0)
        except Exception:
            pass
        return None

    def _parse_rss_time(self, time_str: str) -> datetime | None:
        """Parse RFC 2822 time strings from RSS feeds.

        Args:
            time_str: Time string in RFC 2822 format (e.g., "Tue, 03 Mar 2026 14:00:00 GMT").

        Returns:
            Parsed datetime object or None if parsing fails.
        """
        if not time_str:
            return None

        time_str = time_str.strip()

        formats = [
            "%a, %d %b %Y %H:%M:%S %z",
            "%a, %d %b %Y %H:%M:%S %Z",
            "%d %b %Y %H:%M:%S %z",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(time_str, fmt)
            except ValueError:
                continue
            except Exception:
                continue

        try:
            from email.utils import parsedate_to_datetime

            return parsedate_to_datetime(time_str)
        except Exception:
            pass

        logger.debug("Could not parse RSS time string: %s", time_str)
        return None

    def _strip_html(self, html: str) -> str:
        """Remove HTML tags from a string.

        Args:
            html: String potentially containing HTML.

        Returns:
            Plain text with HTML tags removed.
        """
        if not html:
            return ""

        text = re.sub(r"<[^>]+>", "", html)
        text = re.sub(r"\s+", " ", text)
        return text.strip()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    client = GoogleNewsClient()

    print("\n=== Testing Google News Scraper ===\n")

    articles = client.search("TCS stock", max_results=10)

    print(f"Found {len(articles)} articles:\n")

    for i, article in enumerate(articles, 1):
        print(f"{i}. {article['title']}")
        print(f"   Source: {article['source_name']}")
        print(f"   URL: {article['url']}")
        print(f"   Published: {article['published_at']}")
        if article["content"]:
            print(f"   Snippet: {article['content'][:100]}...")
        print()
