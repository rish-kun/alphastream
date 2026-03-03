"""Debug test scripts for the deep research functionality.

This module provides comprehensive test cases to debug the extensive research
pipeline, including individual scrapers, the _run_scrapers function,
_store_research_articles, and the complete research_topic task flow.

Run with:
    cd /Users/rishit/Coding/alphastream/pipeline && python -m pytest tests/test_deep_research_debug.py -v -s
"""

import logging
import sys
import uuid
from datetime import datetime, UTC
from unittest.mock import MagicMock, patch

import pytest

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

sys.path.insert(0, "/Users/rishit/Coding/alphastream/pipeline")


class TestFirecrawlScraper:
    """Tests for Firecrawl scraper with sample query 'iran'."""

    def test_firecrawl_search_indian_financial_news(self):
        """Test Firecrawl scraper with sample query 'iran'."""
        logger.info("=" * 80)
        logger.info("TEST: Firecrawl scraper with query 'iran'")
        logger.info("=" * 80)

        from pipeline.scrapers.firecrawl_client import FirecrawlClient
        from pipeline.config import settings

        logger.info(f"Firecrawl API Key configured: {bool(settings.FIRECRAWL_API_KEY)}")
        if settings.FIRECRAWL_API_KEY:
            masked_key = (
                f"{settings.FIRECRAWL_API_KEY[:4]}...{settings.FIRECRAWL_API_KEY[-4:]}"
            )
            logger.info(f"Firecrawl API Key (masked): {masked_key}")

        client = FirecrawlClient()

        try:
            results = client.search_indian_financial_news("iran", limit=5)
            logger.info(f"Firecrawl returned {len(results)} articles for query 'iran'")

            for i, article in enumerate(results, 1):
                logger.info(
                    f"  Article {i}: {article.get('title', 'No title')[:60]}..."
                )
                logger.info(f"    URL: {article.get('url', 'No URL')}")
                logger.info(f"    Source: {article.get('source_name', 'Unknown')}")
                logger.info(f"    Published: {article.get('published_at', 'Unknown')}")
                content_preview = (article.get("content") or "")[:100]
                logger.info(f"    Content preview: {content_preview}...")

            assert isinstance(results, list), "Results should be a list"

        except Exception as e:
            logger.error(f"Firecrawl scraper failed: {str(e)}", exc_info=True)
            raise

    def test_firecrawl_scrape_url(self):
        """Test Firecrawl URL scraping with a sample URL."""
        logger.info("=" * 80)
        logger.info("TEST: Firecrawl URL scraping")
        logger.info("=" * 80)

        from pipeline.scrapers.firecrawl_client import FirecrawlClient
        from pipeline.config import settings

        if not settings.FIRECRAWL_API_KEY:
            pytest.skip("Firecrawl API key not configured")

        client = FirecrawlClient()
        test_url = "https://www.reuters.com/world/middle-east/iran-news/"

        try:
            result = client.scrape_url(test_url)
            if result:
                logger.info(f"Scraped URL: {result.get('url')}")
                logger.info(f"Title: {result.get('title')}")
                logger.info(f"Content length: {len(result.get('content', ''))}")
            else:
                logger.warning("URL scraping returned None")
        except Exception as e:
            logger.error(f"Firecrawl URL scraping failed: {str(e)}", exc_info=True)


class TestThunderbitScraper:
    """Tests for Thunderbit scraper with sample query 'iran'."""

    def test_thunderbit_search_and_scrape(self):
        """Test Thunderbit scraper with sample query 'iran'."""
        logger.info("=" * 80)
        logger.info("TEST: Thunderbit scraper with query 'iran'")
        logger.info("=" * 80)

        from pipeline.scrapers.thunderbit_client import ThunderbitClient
        from pipeline.config import settings

        logger.info(
            f"Thunderbit API Key configured: {bool(settings.THUNDERBIT_API_KEY)}"
        )
        if settings.THUNDERBIT_API_KEY:
            masked_key = f"{settings.THUNDERBIT_API_KEY[:4]}...{settings.THUNDERBIT_API_KEY[-4:]}"
            logger.info(f"Thunderbit API Key (masked): {masked_key}")

        client = ThunderbitClient()

        try:
            results = client.search_and_scrape("iran", limit=5)
            logger.info(f"Thunderbit returned {len(results)} articles for query 'iran'")

            for i, article in enumerate(results, 1):
                logger.info(
                    f"  Article {i}: {article.get('title', 'No title')[:60]}..."
                )
                logger.info(f"    URL: {article.get('url', 'No URL')}")
                logger.info(f"    Source: {article.get('source_name', 'Unknown')}")

            assert isinstance(results, list), "Results should be a list"

        except Exception as e:
            logger.error(f"Thunderbit scraper failed: {str(e)}", exc_info=True)
            raise

    def test_thunderbit_scrape_url(self):
        """Test Thunderbit URL scraping with a sample URL."""
        logger.info("=" * 80)
        logger.info("TEST: Thunderbit URL scraping")
        logger.info("=" * 80)

        from pipeline.scrapers.thunderbit_client import ThunderbitClient
        from pipeline.config import settings

        if not settings.THUNDERBIT_API_KEY:
            pytest.skip("Thunderbit API key not configured")

        client = ThunderbitClient()
        test_url = "https://www.reuters.com/world/middle-east/iran-news/"

        try:
            result = client.scrape_url(test_url)
            if result:
                logger.info(f"Scraped URL: {result.get('url')}")
                logger.info(f"Title: {result.get('title')}")
                logger.info(f"Content length: {len(result.get('content', ''))}")
            else:
                logger.warning("URL scraping returned None")
        except Exception as e:
            logger.error(f"Thunderbit URL scraping failed: {str(e)}", exc_info=True)


class TestBrowseAIScraper:
    """Tests for Browse.ai scraper with sample query 'iran'."""

    def test_browseai_search_financial_news(self):
        """Test Browse.ai scraper with sample query 'iran'."""
        logger.info("=" * 80)
        logger.info("TEST: Browse.ai scraper with query 'iran'")
        logger.info("=" * 80)

        from pipeline.scrapers.browseai_client import BrowseAIClient
        from pipeline.config import settings

        logger.info(f"Browse.ai API Key configured: {bool(settings.BROWSEAI_API_KEY)}")
        logger.info(f"Browse.ai Team ID configured: {bool(settings.BROWSEAI_TEAM_ID)}")
        logger.info(
            f"Browse.ai Default Robot ID configured: {bool(settings.BROWSEAI_DEFAULT_ROBOT_ID)}"
        )

        if settings.BROWSEAI_API_KEY:
            masked_key = (
                f"{settings.BROWSEAI_API_KEY[:4]}...{settings.BROWSEAI_API_KEY[-4:]}"
            )
            logger.info(f"Browse.ai API Key (masked): {masked_key}")
        if settings.BROWSEAI_DEFAULT_ROBOT_ID:
            logger.info(f"Browse.ai Robot ID: {settings.BROWSEAI_DEFAULT_ROBOT_ID}")

        client = BrowseAIClient()

        try:
            results = client.search_financial_news("iran")
            logger.info(f"Browse.ai returned {len(results)} articles for query 'iran'")

            for i, article in enumerate(results, 1):
                logger.info(
                    f"  Article {i}: {article.get('title', 'No title')[:60]}..."
                )
                logger.info(f"    URL: {article.get('url', 'No URL')}")
                logger.info(f"    Source: {article.get('source_name', 'Unknown')}")

            assert isinstance(results, list), "Results should be a list"

        except Exception as e:
            logger.error(f"Browse.ai scraper failed: {str(e)}", exc_info=True)
            raise


class TestRunScrapers:
    """Tests for the _run_scrapers function from extensive_research.py."""

    def test_run_scrapers_with_iran_query(self):
        """Test _run_scrapers function with sample query 'iran'."""
        logger.info("=" * 80)
        logger.info("TEST: _run_scrapers function with query 'iran'")
        logger.info("=" * 80)

        from pipeline.tasks.extensive_research import _run_scrapers

        try:
            results = _run_scrapers("iran", limit=5)
            logger.info(f"_run_scrapers returned {len(results)} total articles")

            firecrawl_count = sum(
                1 for r in results if r.get("scraper_source") == "firecrawl"
            )
            thunderbit_count = sum(
                1 for r in results if r.get("scraper_source") == "thunderbit"
            )
            browseai_count = sum(
                1 for r in results if r.get("scraper_source") == "browseai"
            )

            logger.info(f"  - Firecrawl: {firecrawl_count} articles")
            logger.info(f"  - Thunderbit: {thunderbit_count} articles")
            logger.info(f"  - Browse.ai: {browseai_count} articles")

            for i, article in enumerate(results, 1):
                logger.info(
                    f"  Article {i}: {article.get('title', 'No title')[:50]}..."
                )
                logger.info(
                    f"    Source: {article.get('scraper_source', 'Unknown scraper')}"
                )
                logger.info(f"    URL: {article.get('url', 'No URL')[:60]}...")

            assert isinstance(results, list), "Results should be a list"

        except Exception as e:
            logger.error(f"_run_scrapers failed: {str(e)}", exc_info=True)
            raise


class TestStoreResearchArticles:
    """Tests for the _store_research_articles function with mock data."""

    def test_store_research_articles_with_mock_data(self):
        """Test _store_research_articles with mock article data."""
        logger.info("=" * 80)
        logger.info("TEST: _store_research_articles with mock data")
        logger.info("=" * 80)

        from pipeline.tasks.extensive_research import _store_research_articles
        from pipeline.database import check_schema_ready

        schema_ready = check_schema_ready()
        logger.info(f"Database schema ready: {schema_ready}")

        if not schema_ready:
            pytest.skip("Database schema not ready - run migrations first")

        mock_articles = [
            {
                "title": f"Test Iran Article {i}",
                "url": f"https://example.com/iran-article-{i}-{uuid.uuid4()}.html",
                "content": f"This is test content for Iran article {i}. " * 10,
                "source_name": "Example News",
                "published_at": datetime.now(UTC).isoformat(),
                "scraper_source": "test",
            }
            for i in range(1, 4)
        ]

        logger.info(f"Mock articles to store: {len(mock_articles)}")
        for i, article in enumerate(mock_articles, 1):
            logger.info(f"  {i}. {article['title']}")
            logger.info(f"     URL: {article['url']}")

        try:
            new_count, article_ids = _store_research_articles(
                mock_articles, source_query="iran test query"
            )
            logger.info(f"Stored {new_count} new articles")
            logger.info(f"Article IDs: {article_ids}")

            assert isinstance(new_count, int), "new_count should be an integer"
            assert isinstance(article_ids, list), "article_ids should be a list"

        except Exception as e:
            logger.error(f"_store_research_articles failed: {str(e)}", exc_info=True)
            raise

    def test_store_research_articles_deduplication(self):
        """Test that _store_research_articles correctly deduplicates by URL."""
        logger.info("=" * 80)
        logger.info("TEST: _store_research_articles deduplication")
        logger.info("=" * 80)

        from pipeline.tasks.extensive_research import _store_research_articles
        from pipeline.database import check_schema_ready

        if not check_schema_ready():
            pytest.skip("Database schema not ready")

        duplicate_url = f"https://example.com/duplicate-test-{uuid.uuid4()}.html"

        mock_articles = [
            {
                "title": "Duplicate Article 1",
                "url": duplicate_url,
                "content": "Content for duplicate article 1",
                "source_name": "Test Source",
                "published_at": datetime.now(UTC).isoformat(),
                "scraper_source": "test",
            },
            {
                "title": "Duplicate Article 2",
                "url": duplicate_url,
                "content": "Content for duplicate article 2",
                "source_name": "Test Source",
                "published_at": datetime.now(UTC).isoformat(),
                "scraper_source": "test",
            },
            {
                "title": "Unique Article",
                "url": f"https://example.com/unique-{uuid.uuid4()}.html",
                "content": "Content for unique article",
                "source_name": "Test Source",
                "published_at": datetime.now(UTC).isoformat(),
                "scraper_source": "test",
            },
        ]

        logger.info("Testing with 2 duplicate URLs and 1 unique URL")

        try:
            new_count, article_ids = _store_research_articles(
                mock_articles, source_query="deduplication test"
            )
            logger.info(f"Stored {new_count} new articles (expected: 2)")

            assert new_count <= 2, (
                "Should store at most 2 articles (1 unique + 1 duplicate)"
            )

        except Exception as e:
            logger.error(f"Deduplication test failed: {str(e)}", exc_info=True)
            raise


class TestResearchTopicTask:
    """Tests for the complete research_topic task flow."""

    def test_research_topic_task_flow(self):
        """Test the complete research_topic task flow with query 'iran'."""
        logger.info("=" * 80)
        logger.info("TEST: Complete research_topic task flow with query 'iran'")
        logger.info("=" * 80)

        from pipeline.database import check_schema_ready

        schema_ready = check_schema_ready()
        logger.info(f"Database schema ready: {schema_ready}")

        if not schema_ready:
            pytest.skip("Database schema not ready - run migrations first")

        test_topic = "iran"
        test_user_id = "debug-test-user"

        logger.info(
            f"Testing research_topic with topic='{test_topic}', user_id='{test_user_id}'"
        )

        try:
            from pipeline.tasks.extensive_research import research_topic

            result = research_topic.apply(args=[test_topic, test_user_id])

            logger.info(f"Task status: {result.status}")

            if result.status == "SUCCESS":
                result_data = result.result
                logger.info(f"Result: {result_data}")

                logger.info(f"  Status: {result_data.get('status')}")
                logger.info(f"  Topic: {result_data.get('topic')}")
                logger.info(f"  New articles: {result_data.get('new_articles')}")
                logger.info(f"  Total found: {result_data.get('total_found')}")
                logger.info(f"  Query count: {result_data.get('query_count')}")
                logger.info(f"  Duration: {result_data.get('duration_seconds')}s")
                logger.info(
                    f"  Article IDs: {len(result_data.get('article_ids', []))} articles"
                )

                assert result_data.get("status") == "completed", (
                    "Task should complete successfully"
                )
                assert isinstance(result_data.get("new_articles"), int), (
                    "new_articles should be an integer"
                )
            else:
                logger.error(f"Task failed with status: {result.status}")
                if result.result:
                    logger.error(f"Error: {result.result}")
                pytest.fail(f"Task failed with status: {result.status}")

        except Exception as e:
            logger.error(f"research_topic task flow failed: {str(e)}", exc_info=True)
            raise


class TestDatabaseConnection:
    """Tests for database connection status."""

    def test_database_connection(self):
        """Test database connection and schema."""
        logger.info("=" * 80)
        logger.info("TEST: Database connection status")
        logger.info("=" * 80)

        from pipeline.database import get_engine, check_schema_ready
        from pipeline.config import settings

        logger.info(
            f"Database URL: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}"
        )

        try:
            engine = get_engine()
            with engine.connect() as conn:
                result = conn.execute(__import__("sqlalchemy").text("SELECT 1"))
                logger.info(f"Database connection test: {result.scalar()}")

            schema_ready = check_schema_ready()
            logger.info(f"Schema ready: {schema_ready}")

            if schema_ready:
                from pipeline.database import _REQUIRED_TABLES

                logger.info(f"Required tables: {', '.join(sorted(_REQUIRED_TABLES))}")

        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}", exc_info=True)
            raise


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
