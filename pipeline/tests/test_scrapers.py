"""Tests for scraper modules — RSS, Article, Firecrawl, BrowseAI, Thunderbit."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# RSS Feed Parser
# ---------------------------------------------------------------------------


class TestRSSFeedParser:
    """Tests for pipeline.scrapers.rss_feeds.RSSFeedParser."""

    def _make_entry(
        self,
        title="Test",
        summary="Sum",
        link="http://x.com/1",
        published_parsed=(2025, 1, 1, 0, 0, 0, 0, 0, 0),
        source_title="Src",
    ):
        """Build a fake feedparser entry with attribute access."""
        entry = SimpleNamespace(
            title=title,
            summary=summary,
            link=link,
            published_parsed=published_parsed,
            source={"title": source_title},
        )
        return entry

    @patch("pipeline.scrapers.rss_feeds.feedparser")
    def test_fetch_feed_returns_normalized_articles(self, mock_fp):
        """parse() should return a list of normalized dicts."""
        from pipeline.scrapers.rss_feeds import RSSFeedParser

        entry = self._make_entry()
        mock_fp.parse.return_value = SimpleNamespace(
            bozo=False,
            bozo_exception=None,
            entries=[entry],
        )

        parser = RSSFeedParser()
        results = parser.fetch_feed("http://feed.example.com/rss")

        assert isinstance(results, list)
        assert len(results) == 1
        assert results[0]["title"] == "Test"
        assert results[0]["link"] == "http://x.com/1"
        assert results[0]["summary"] == "Sum"
        assert results[0]["published"] is not None
        mock_fp.parse.assert_called_once()

    @patch("pipeline.scrapers.rss_feeds.feedparser")
    def test_fetch_feed_handles_bozo(self, mock_fp):
        """Bozo feeds should still return entries without raising."""
        from pipeline.scrapers.rss_feeds import RSSFeedParser

        entry = self._make_entry()
        mock_fp.parse.return_value = SimpleNamespace(
            bozo=True,
            bozo_exception=Exception("bad feed"),
            entries=[entry],
        )

        parser = RSSFeedParser()
        results = parser.fetch_feed("http://bad.feed")

        assert len(results) == 1

    def test_parse_entry_missing_fields(self):
        """parse_entry should handle entries with missing attributes gracefully."""
        from pipeline.scrapers.rss_feeds import RSSFeedParser

        # An entry with no title, no summary, no link, no published, no source
        entry = SimpleNamespace()
        parser = RSSFeedParser()
        result = parser.parse_entry(entry)

        assert result["title"] == ""
        assert result["summary"] == ""
        assert result["link"] == ""
        assert result["published"] is None
        assert result["source"] == ""

    def test_deduplicate_removes_duplicate_links(self):
        """deduplicate() should remove entries with the same link."""
        from pipeline.scrapers.rss_feeds import RSSFeedParser

        entries = [
            {"title": "A", "link": "http://a.com"},
            {"title": "B", "link": "http://a.com"},
            {"title": "C", "link": "http://c.com"},
        ]
        parser = RSSFeedParser()
        result = parser.deduplicate(entries)

        assert len(result) == 2
        assert result[0]["title"] == "A"
        assert result[1]["title"] == "C"

    def test_deduplicate_skips_empty_links(self):
        """Entries without a link should not be counted as duplicates of each other."""
        from pipeline.scrapers.rss_feeds import RSSFeedParser

        entries = [
            {"title": "X", "link": ""},
            {"title": "Y", "link": ""},
        ]
        parser = RSSFeedParser()
        result = parser.deduplicate(entries)

        # Both have empty links — neither is added (empty link is falsy)
        assert len(result) == 0


# ---------------------------------------------------------------------------
# Article Scraper
# ---------------------------------------------------------------------------


class TestArticleScraper:
    """Tests for pipeline.scrapers.article_scraper.ArticleScraper."""

    @patch("newspaper.Article")
    def test_scrape_returns_cleaned_text(self, MockArticle):
        """scrape() should download, parse, and return cleaned text."""
        from pipeline.scrapers.article_scraper import ArticleScraper

        mock_article = MagicMock()
        mock_article.text = "Reliance Industries   reported strong  growth."
        MockArticle.return_value = mock_article

        scraper = ArticleScraper()
        result = scraper.scrape("http://example.com/article")

        assert result is not None
        assert "Reliance Industries" in result
        mock_article.download.assert_called_once()
        mock_article.parse.assert_called_once()

    @patch("newspaper.Article")
    def test_scrape_returns_none_on_empty_text(self, MockArticle):
        """scrape() should return None when article text is empty."""
        from pipeline.scrapers.article_scraper import ArticleScraper

        mock_article = MagicMock()
        mock_article.text = ""
        MockArticle.return_value = mock_article

        scraper = ArticleScraper()
        result = scraper.scrape("http://example.com/empty")

        assert result is None

    @patch("newspaper.Article", side_effect=Exception("timeout"))
    def test_scrape_returns_none_on_exception(self, MockArticle):
        """scrape() should return None when newspaper raises an exception."""
        from pipeline.scrapers.article_scraper import ArticleScraper

        scraper = ArticleScraper()
        result = scraper.scrape("http://example.com/bad")

        assert result is None

    def test_clean_text_removes_boilerplate(self):
        """clean_text should remove common boilerplate patterns."""
        from pipeline.scrapers.article_scraper import ArticleScraper

        scraper = ArticleScraper()
        raw = "Great results. Also read: more news here. Follow us on Twitter for updates."
        cleaned = scraper.clean_text(raw)

        assert "Also read" not in cleaned
        assert "Follow us on Twitter" not in cleaned


# ---------------------------------------------------------------------------
# Firecrawl Client
# ---------------------------------------------------------------------------


class TestFirecrawlClient:
    """Tests for pipeline.scrapers.firecrawl_client.FirecrawlClient."""

    @patch("pipeline.scrapers.firecrawl_client.settings")
    def test_search_news_returns_normalized_articles(self, mock_settings):
        """search_news() should normalise SDK response into article dicts."""
        mock_settings.FIRECRAWL_API_KEY = "test-key"

        from pipeline.scrapers.firecrawl_client import FirecrawlClient

        client = FirecrawlClient()

        mock_app = MagicMock()
        mock_app.search.return_value = [
            {
                "title": "Sensex Rises",
                "url": "http://moneycontrol.com/article",
                "markdown": "Full article content",
                "published_at": "2025-01-01",
            }
        ]
        client._app = mock_app

        results = client.search_news("Sensex", limit=5)

        assert len(results) == 1
        assert results[0]["title"] == "Sensex Rises"
        assert results[0]["url"] == "http://moneycontrol.com/article"
        assert results[0]["content"] == "Full article content"
        assert results[0]["scraper_source"] == "firecrawl"

    @patch("pipeline.scrapers.firecrawl_client.settings")
    def test_search_news_returns_empty_on_no_api_key(self, mock_settings):
        """search_news() returns [] when API key is missing."""
        mock_settings.FIRECRAWL_API_KEY = ""

        from pipeline.scrapers.firecrawl_client import FirecrawlClient

        client = FirecrawlClient()
        client._app = None  # force lazy init path

        results = client.search_news("anything")
        assert results == []

    @patch("pipeline.scrapers.firecrawl_client.settings")
    def test_scrape_url_returns_content(self, mock_settings):
        """scrape_url() should return a normalised dict."""
        mock_settings.FIRECRAWL_API_KEY = "key"

        from pipeline.scrapers.firecrawl_client import FirecrawlClient

        client = FirecrawlClient()
        mock_app = MagicMock()
        mock_app.scrape.return_value = {
            "data": {
                "title": "Article Title",
                "markdown": "Markdown content",
            }
        }
        client._app = mock_app

        result = client.scrape_url("http://example.com/page")

        assert result is not None
        assert result["title"] == "Article Title"
        assert result["content"] == "Markdown content"
        assert result["scraper_source"] == "firecrawl"

    @patch("pipeline.scrapers.firecrawl_client.settings")
    def test_scrape_url_returns_none_on_exception(self, mock_settings):
        """scrape_url() returns None when the SDK raises."""
        mock_settings.FIRECRAWL_API_KEY = "key"

        from pipeline.scrapers.firecrawl_client import FirecrawlClient

        client = FirecrawlClient()
        mock_app = MagicMock()
        mock_app.scrape.side_effect = Exception("API error")
        client._app = mock_app

        result = client.scrape_url("http://example.com/bad")
        assert result is None

    def test_extract_source_name(self):
        """_extract_source_name should strip www./m. prefixes."""
        from pipeline.scrapers.firecrawl_client import FirecrawlClient

        assert (
            FirecrawlClient._extract_source_name("https://www.moneycontrol.com/x")
            == "moneycontrol.com"
        )
        assert (
            FirecrawlClient._extract_source_name("https://m.livemint.com/y")
            == "livemint.com"
        )
        assert FirecrawlClient._extract_source_name("not-a-url") == ""


# ---------------------------------------------------------------------------
# Browse.ai Client
# ---------------------------------------------------------------------------


class TestBrowseAIClient:
    """Tests for pipeline.scrapers.browseai_client.BrowseAIClient."""

    @patch("pipeline.scrapers.browseai_client.settings")
    @patch("pipeline.scrapers.browseai_client.httpx.Client")
    def test_trigger_robot_returns_task_id(self, MockHTTPClient, mock_settings):
        """trigger_robot() should return the task ID from Browse.ai."""
        mock_settings.BROWSEAI_API_KEY = "test-key"
        mock_settings.BROWSEAI_DEFAULT_ROBOT_ID = "robot-1"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": {"id": "task-123"}}

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = MagicMock(return_value=False)
        mock_client_instance.post.return_value = mock_response
        MockHTTPClient.return_value = mock_client_instance

        from pipeline.scrapers.browseai_client import BrowseAIClient

        client = BrowseAIClient()
        task_id = client.trigger_robot("robot-1", {"url": "http://x.com"})

        assert task_id == "task-123"

    @patch("pipeline.scrapers.browseai_client.settings")
    @patch("pipeline.scrapers.browseai_client.httpx.Client")
    def test_trigger_robot_returns_none_on_http_error(
        self, MockHTTPClient, mock_settings
    ):
        """trigger_robot() returns None on non-200 response."""
        mock_settings.BROWSEAI_API_KEY = "test-key"
        mock_settings.BROWSEAI_DEFAULT_ROBOT_ID = "robot-1"

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Server Error"

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = MagicMock(return_value=False)
        mock_client_instance.post.return_value = mock_response
        MockHTTPClient.return_value = mock_client_instance

        from pipeline.scrapers.browseai_client import BrowseAIClient

        client = BrowseAIClient()
        task_id = client.trigger_robot("robot-1", {"url": "http://x.com"})

        assert task_id is None

    @patch("pipeline.scrapers.browseai_client.settings")
    def test_trigger_robot_returns_none_without_api_key(self, mock_settings):
        """trigger_robot() returns None when API key is not set."""
        mock_settings.BROWSEAI_API_KEY = ""
        mock_settings.BROWSEAI_DEFAULT_ROBOT_ID = ""

        from pipeline.scrapers.browseai_client import BrowseAIClient

        client = BrowseAIClient()
        task_id = client.trigger_robot("robot-1", {"url": "http://x.com"})

        assert task_id is None


# ---------------------------------------------------------------------------
# Thunderbit Client
# ---------------------------------------------------------------------------


class TestThunderbitClient:
    """Tests for pipeline.scrapers.thunderbit_client.ThunderbitClient."""

    @patch("pipeline.scrapers.thunderbit_client.settings")
    @patch("pipeline.scrapers.thunderbit_client.httpx.Client")
    def test_scrape_url_returns_content(self, MockHTTPClient, mock_settings):
        """scrape_url() should return a normalised article dict."""
        mock_settings.THUNDERBIT_API_KEY = "test-key"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "title": "Market Update",
                "markdown": "Article body in markdown",
                "published_at": "2025-01-15",
            }
        }

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = MagicMock(return_value=False)
        mock_client_instance.post.return_value = mock_response
        MockHTTPClient.return_value = mock_client_instance

        from pipeline.scrapers.thunderbit_client import ThunderbitClient

        client = ThunderbitClient()
        result = client.scrape_url("http://example.com/article")

        assert result is not None
        assert result["title"] == "Market Update"
        assert result["content"] == "Article body in markdown"
        assert result["scraper_source"] == "thunderbit"

    @patch("pipeline.scrapers.thunderbit_client.settings")
    @patch("pipeline.scrapers.thunderbit_client.httpx.Client")
    def test_scrape_url_returns_none_on_error(self, MockHTTPClient, mock_settings):
        """scrape_url() returns None on non-200 status."""
        mock_settings.THUNDERBIT_API_KEY = "test-key"

        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = "Rate limited"

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = MagicMock(return_value=False)
        mock_client_instance.post.return_value = mock_response
        MockHTTPClient.return_value = mock_client_instance

        from pipeline.scrapers.thunderbit_client import ThunderbitClient

        client = ThunderbitClient()
        result = client.scrape_url("http://example.com/limited")

        assert result is None

    @patch("pipeline.scrapers.thunderbit_client.settings")
    def test_scrape_url_returns_none_without_api_key(self, mock_settings):
        """scrape_url() returns None when API key is missing."""
        mock_settings.THUNDERBIT_API_KEY = ""

        from pipeline.scrapers.thunderbit_client import ThunderbitClient

        client = ThunderbitClient()
        result = client.scrape_url("http://example.com/x")

        assert result is None

    def test_extract_source_name(self):
        """_extract_source_name strips common prefixes."""
        from pipeline.scrapers.thunderbit_client import ThunderbitClient

        assert (
            ThunderbitClient._extract_source_name("https://www.example.com/p")
            == "example.com"
        )
        assert (
            ThunderbitClient._extract_source_name("https://amp.livemint.com/a")
            == "livemint.com"
        )
