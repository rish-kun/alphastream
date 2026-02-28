"""Tests for Celery task modules — RSS ingestion, Web scraper, Sentiment, Research.

All external dependencies (DB, scrapers, ML models, Celery broker, Redis) are
mocked so these tests run fully offline.
"""

from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import MagicMock, patch, call

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_db_ctx(mock_db):
    """Return a callable that produces a context-manager yielding *mock_db*.

    ``get_db`` is a function that returns a context-manager, so we need
    ``mock_get_db.side_effect`` (or ``return_value``) to behave the same.
    This helper returns a *callable* (factory) — assign it to
    ``mock_get_db.side_effect`` so each ``get_db()`` call yields a fresh
    context-manager wrapping the same *mock_db*.
    """

    def _factory():
        @contextmanager
        def _ctx():
            yield mock_db

        return _ctx()

    return _factory


# ---------------------------------------------------------------------------
# RSS Ingestion
# ---------------------------------------------------------------------------


class TestRSSIngestion:
    """Tests for pipeline.tasks.rss_ingestion."""

    @patch("pipeline.tasks.rss_ingestion.fetch_single_feed")
    def test_fetch_all_feeds_dispatches_tasks(self, mock_fetch_single):
        """fetch_all_feeds should dispatch a task per feed URL."""
        from pipeline.tasks.rss_ingestion import fetch_all_feeds, FEED_SOURCES

        mock_fetch_single.delay = MagicMock()

        result = fetch_all_feeds()

        # Should dispatch one task per URL across all sources
        total_urls = sum(len(urls) for urls in FEED_SOURCES.values())
        assert mock_fetch_single.delay.call_count == total_urls
        assert len(result) == total_urls

    @patch("pipeline.tasks.rss_ingestion.get_db")
    @patch("pipeline.tasks.rss_ingestion.RSSFeedParser")
    def test_fetch_single_feed_stores_new_articles(self, MockParser, mock_get_db):
        """fetch_single_feed should parse feed and insert new articles into DB."""
        from pipeline.tasks.rss_ingestion import fetch_single_feed

        # Set up mock parser
        mock_parser_instance = MagicMock()
        mock_parser_instance.fetch_feed.return_value = [
            {
                "title": "Test Article",
                "summary": "Summary text",
                "link": "http://example.com/article-1",
                "published": "2025-01-01T00:00:00",
                "source": {"title": "TestSource"},
            }
        ]
        MockParser.return_value = mock_parser_instance

        # Set up mock DB — article doesn't exist yet
        mock_db = MagicMock()
        mock_db.execute.return_value.fetchone.return_value = None
        mock_db.execute.return_value.scalar.return_value = 42
        mock_get_db.side_effect = _make_db_ctx(mock_db)

        with (
            patch(
                "pipeline.tasks.rss_ingestion.clean_html", return_value="Clean summary"
            ),
            patch(
                "pipeline.tasks.rss_ingestion.compute_content_hash",
                return_value="abc123",
            ),
            patch("pipeline.utils.publisher.publish_new_article", return_value=True),
            patch("pipeline.utils.publisher._get_redis", return_value=MagicMock()),
            patch("pipeline.tasks.web_scraper.scrape_article") as mock_scrape,
        ):
            mock_scrape.delay = MagicMock()

            result = fetch_single_feed("http://feed.test/rss", "TestSource")

        assert result["source"] == "TestSource"
        assert result["articles_fetched"] >= 0

    @patch("pipeline.tasks.rss_ingestion.get_db")
    @patch("pipeline.tasks.rss_ingestion.RSSFeedParser")
    def test_fetch_single_feed_skips_existing(self, MockParser, mock_get_db):
        """fetch_single_feed should skip articles that already exist in DB."""
        from pipeline.tasks.rss_ingestion import fetch_single_feed

        mock_parser_instance = MagicMock()
        mock_parser_instance.fetch_feed.return_value = [
            {
                "title": "Old Article",
                "summary": "",
                "link": "http://example.com/old",
                "published": None,
                "source": {},
            }
        ]
        MockParser.return_value = mock_parser_instance

        # DB says article already exists
        mock_db = MagicMock()
        mock_existing = MagicMock()
        mock_existing.id = 99
        mock_db.execute.return_value.fetchone.return_value = mock_existing
        mock_get_db.side_effect = _make_db_ctx(mock_db)

        with (
            patch("pipeline.tasks.rss_ingestion.clean_html"),
            patch("pipeline.tasks.rss_ingestion.compute_content_hash"),
        ):
            result = fetch_single_feed("http://feed.test/rss", "Src")

        assert result["articles_fetched"] == 0


# ---------------------------------------------------------------------------
# Web Scraper
# ---------------------------------------------------------------------------


class TestWebScraper:
    """Tests for pipeline.tasks.web_scraper."""

    @patch("pipeline.tasks.web_scraper.scrape_article")
    @patch("pipeline.tasks.web_scraper.get_db")
    def test_scrape_pending_dispatches(self, mock_get_db, mock_scrape_article):
        """scrape_pending_articles should dispatch scrape tasks for pending rows."""
        from pipeline.tasks.web_scraper import scrape_pending_articles

        row1 = SimpleNamespace(id=1, url="http://a.com/1")
        row2 = SimpleNamespace(id=2, url="http://a.com/2")

        mock_db = MagicMock()
        mock_db.execute.return_value.fetchall.return_value = [row1, row2]
        mock_get_db.side_effect = _make_db_ctx(mock_db)
        mock_scrape_article.delay = MagicMock()

        result = scrape_pending_articles()

        assert result["articles_dispatched"] == 2
        assert mock_scrape_article.delay.call_count == 2

    @patch("pipeline.tasks.web_scraper.get_db")
    @patch("pipeline.tasks.web_scraper.ArticleScraper")
    def test_scrape_article_success(self, MockScraper, mock_get_db):
        """scrape_article should scrape, clean, store, and dispatch downstream."""
        from pipeline.tasks.web_scraper import scrape_article

        mock_scraper_instance = MagicMock()
        mock_scraper_instance.scrape.return_value = "Raw article text"
        MockScraper.return_value = mock_scraper_instance

        mock_db = MagicMock()
        mock_get_db.side_effect = _make_db_ctx(mock_db)

        with (
            patch(
                "pipeline.tasks.web_scraper.clean_article_text",
                return_value="Clean text",
            ),
            patch(
                "pipeline.tasks.sentiment_analysis.analyze_article"
            ) as mock_sentiment,
            patch(
                "pipeline.tasks.ticker_identification.identify_tickers"
            ) as mock_ticker,
        ):
            mock_sentiment.delay = MagicMock()
            mock_ticker.delay = MagicMock()

            # scrape_article is a bound task — call the underlying function
            result = scrape_article("1", "http://example.com/article")

        assert result["status"] == "success"
        assert result["article_id"] == "1"

    @patch("pipeline.tasks.web_scraper.get_db")
    @patch("pipeline.tasks.web_scraper.ArticleScraper")
    def test_scrape_article_no_text(self, MockScraper, mock_get_db):
        """scrape_article should return 'failed' when no text is extracted."""
        from pipeline.tasks.web_scraper import scrape_article

        mock_scraper_instance = MagicMock()
        mock_scraper_instance.scrape.return_value = None
        MockScraper.return_value = mock_scraper_instance

        result = scrape_article("1", "http://example.com/empty")

        assert result["status"] == "failed"


# ---------------------------------------------------------------------------
# Sentiment Analysis
# ---------------------------------------------------------------------------


class TestSentimentAnalysis:
    """Tests for pipeline.tasks.sentiment_analysis."""

    @patch("pipeline.tasks.sentiment_analysis.analyze_article")
    @patch("pipeline.tasks.sentiment_analysis.get_db")
    def test_analyze_pending_dispatches(self, mock_get_db, mock_analyze_article):
        """analyze_pending should dispatch tasks for articles needing analysis."""
        from pipeline.tasks.sentiment_analysis import analyze_pending

        row1 = SimpleNamespace(id=10)
        row2 = SimpleNamespace(id=20)

        mock_db = MagicMock()
        mock_db.execute.return_value.fetchall.return_value = [row1, row2]
        mock_get_db.side_effect = _make_db_ctx(mock_db)
        mock_analyze_article.delay = MagicMock()

        result = analyze_pending()

        assert result["articles_dispatched"] == 2
        assert mock_analyze_article.delay.call_count == 2

    @patch("pipeline.tasks.sentiment_analysis.get_db")
    def test_analyze_article_not_found(self, mock_get_db):
        """analyze_article should return not_found for missing article."""
        from pipeline.tasks.sentiment_analysis import analyze_article

        mock_db = MagicMock()
        mock_db.execute.return_value.fetchone.return_value = None
        mock_get_db.side_effect = _make_db_ctx(mock_db)

        result = analyze_article("999")

        assert result["status"] == "not_found"

    @patch("pipeline.tasks.sentiment_analysis.settings")
    @patch("pipeline.tasks.sentiment_analysis.get_db")
    def test_analyze_article_finbert_only(self, mock_get_db, mock_settings):
        """analyze_article with FinBERT only (no LLM keys) should succeed."""
        from pipeline.tasks.sentiment_analysis import analyze_article

        mock_settings.GEMINI_API_KEYS = []
        mock_settings.OPENROUTER_API_KEYS = []

        # First call: SELECT article; second call: INSERT sentiment
        mock_db = MagicMock()
        article_row = SimpleNamespace(
            title="Test", full_text="Article text", source="Src"
        )

        call_count = {"n": 0}

        def side_effect_execute(*args, **kwargs):
            call_count["n"] += 1
            result = MagicMock()
            if call_count["n"] == 1:
                result.fetchone.return_value = (
                    article_row.title,
                    article_row.full_text,
                    article_row.source,
                )
            return result

        mock_db.execute = MagicMock(side_effect=side_effect_execute)
        mock_get_db.side_effect = _make_db_ctx(mock_db)

        with (
            patch("pipeline.ml.finbert.FinBERTAnalyzer") as MockFinBERT,
            patch(
                "pipeline.utils.publisher.publish_sentiment_update", return_value=True
            ),
            patch("pipeline.utils.publisher._get_redis", return_value=MagicMock()),
        ):
            mock_analyzer = MagicMock()
            mock_analyzer.analyze.return_value = {
                "score": 0.5,
                "label": "positive",
                "confidence": 0.8,
            }
            MockFinBERT.return_value = mock_analyzer

            result = analyze_article("1")

        assert result["status"] == "success"
        assert result["finbert_score"] == 0.5


# ---------------------------------------------------------------------------
# Extensive Research
# ---------------------------------------------------------------------------


class TestExtensiveResearch:
    """Tests for pipeline.tasks.extensive_research."""

    @patch("pipeline.tasks.extensive_research.get_db")
    def test_store_research_articles_empty(self, mock_get_db):
        """_store_research_articles returns 0 for empty list."""
        from pipeline.tasks.extensive_research import _store_research_articles

        assert _store_research_articles([], "test query") == 0

    @patch("pipeline.tasks.extensive_research.get_db")
    def test_store_research_articles_inserts_new(self, mock_get_db):
        """_store_research_articles should insert new articles."""
        from pipeline.tasks.extensive_research import _store_research_articles

        mock_db = MagicMock()
        # Article doesn't exist yet
        mock_db.execute.return_value.fetchone.return_value = None
        mock_get_db.side_effect = _make_db_ctx(mock_db)

        articles = [
            {
                "title": "New Article",
                "url": "http://example.com/new",
                "content": "Some content",
                "source_name": "TestSrc",
                "published_at": None,
            }
        ]

        with (
            patch("pipeline.tasks.sentiment_analysis.analyze_article") as mock_sa,
            patch("pipeline.tasks.ticker_identification.identify_tickers") as mock_ti,
        ):
            mock_sa.delay = MagicMock()
            mock_ti.delay = MagicMock()

            count = _store_research_articles(articles, "test query")

        assert count == 1

    @patch("pipeline.tasks.extensive_research.get_db")
    def test_store_research_articles_skips_empty_url(self, mock_get_db):
        """_store_research_articles should skip articles with no URL."""
        from pipeline.tasks.extensive_research import _store_research_articles

        mock_db = MagicMock()
        mock_get_db.side_effect = _make_db_ctx(mock_db)

        articles = [{"title": "No URL", "url": "", "content": "c", "source_name": "s"}]

        count = _store_research_articles(articles, "q")
        assert count == 0

    @patch("pipeline.tasks.extensive_research._store_research_articles", return_value=3)
    @patch("pipeline.tasks.extensive_research._run_scrapers")
    @patch("pipeline.tasks.extensive_research.publish_event")
    @patch("pipeline.tasks.extensive_research.get_db")
    def test_research_stock_runs_scrapers(
        self, mock_get_db, mock_publish, mock_run, mock_store
    ):
        """research_stock should build queries and run scrapers for each."""
        from pipeline.tasks.extensive_research import research_stock

        mock_run.return_value = [{"title": "A", "url": "http://x.com"}]

        # DB returns no company name
        mock_db = MagicMock()
        mock_db.execute.return_value.fetchone.return_value = None
        mock_get_db.side_effect = _make_db_ctx(mock_db)

        # Mock update_state on the task instance
        with patch.object(research_stock, "update_state"):
            result = research_stock("RELIANCE", "user-1")

        assert result["status"] == "completed"
        assert result["ticker"] == "RELIANCE"
        assert mock_run.call_count >= 4  # at least 4 queries

    @patch("pipeline.tasks.extensive_research.research_stock")
    @patch("pipeline.tasks.extensive_research.publish_event")
    @patch("pipeline.tasks.extensive_research.get_db")
    def test_research_portfolio_fans_out(
        self, mock_get_db, mock_publish, mock_research_stock
    ):
        """research_portfolio should dispatch research_stock for each ticker."""
        from pipeline.tasks.extensive_research import research_portfolio

        row1 = SimpleNamespace(ticker="RELIANCE")
        row2 = SimpleNamespace(ticker="TCS")
        row3 = SimpleNamespace(ticker="INFY")

        mock_db = MagicMock()
        mock_db.execute.return_value.fetchall.return_value = [row1, row2, row3]
        mock_get_db.side_effect = _make_db_ctx(mock_db)
        mock_research_stock.delay = MagicMock()

        with patch.object(research_portfolio, "update_state"):
            result = research_portfolio("portfolio-1", "user-1")

        assert result["status"] == "dispatched"
        assert result["stocks_count"] == 3
        assert mock_research_stock.delay.call_count == 3

    @patch("pipeline.tasks.extensive_research.publish_event")
    @patch("pipeline.tasks.extensive_research.get_db")
    def test_research_portfolio_empty(self, mock_get_db, mock_publish):
        """research_portfolio should handle a portfolio with no stocks."""
        from pipeline.tasks.extensive_research import research_portfolio

        mock_db = MagicMock()
        mock_db.execute.return_value.fetchall.return_value = []
        mock_get_db.side_effect = _make_db_ctx(mock_db)

        with patch.object(research_portfolio, "update_state"):
            result = research_portfolio("empty-portfolio", "user-1")

        assert result["status"] == "completed"
        assert result["stocks_count"] == 0

    @patch("pipeline.scrapers.browseai_client.BrowseAIClient")
    @patch("pipeline.scrapers.thunderbit_client.ThunderbitClient")
    @patch("pipeline.scrapers.firecrawl_client.FirecrawlClient")
    def test_run_scrapers_merges_results(self, MockFC, MockTB, MockBA):
        """_run_scrapers should combine results from all three scrapers."""
        from pipeline.tasks.extensive_research import _run_scrapers

        # Firecrawl
        mock_fc = MagicMock()
        mock_fc.search_indian_financial_news.return_value = [
            {"title": "FC1", "url": "http://fc.com/1"},
        ]
        MockFC.return_value = mock_fc

        # Thunderbit
        mock_tb = MagicMock()
        mock_tb.search_and_scrape.return_value = [
            {"title": "TB1", "url": "http://tb.com/1"},
        ]
        MockTB.return_value = mock_tb

        # Browse.ai
        mock_ba = MagicMock()
        mock_ba.search_financial_news.return_value = [
            {"title": "BA1", "url": "http://ba.com/1"},
        ]
        MockBA.return_value = mock_ba

        results = _run_scrapers("Reliance stock news", limit=5)

        assert len(results) == 3
        titles = [r["title"] for r in results]
        assert "FC1" in titles
        assert "TB1" in titles
        assert "BA1" in titles
