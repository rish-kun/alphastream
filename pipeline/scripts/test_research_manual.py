#!/usr/bin/env python3
"""Standalone manual test script for deep research functionality.

This script can be run directly to test the research pipeline:
    cd /Users/rishit/Coding/alphastream/pipeline && python scripts/test_research_manual.py --topic "iran"

It tests:
    1. Each scraper individually with detailed output
    2. API key configuration status (masked)
    3. Complete research flow
    4. Database connection status
"""

import argparse
import logging
import sys
import uuid
from datetime import datetime, UTC
from typing import Any

sys.path.insert(0, "/Users/rishit/Coding/alphastream/pipeline")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def print_header(title: str) -> None:
    """Print a formatted header."""
    width = 80
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width)


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n--- {title} ---")


def mask_api_key(key: str, visible_chars: int = 4) -> str:
    """Mask an API key, showing only the first few characters."""
    if not key:
        return "(not configured)"
    if len(key) <= visible_chars * 2:
        return f"{key[:2]}...{key[-2:]}"
    return f"{key[:visible_chars]}...{key[-visible_chars:]}"


def print_api_keys() -> dict[str, bool]:
    """Print and check API key configuration."""
    from pipeline.config import settings

    print_section("API Key Configuration")

    keys_status = {
        "Firecrawl": bool(settings.FIRECRAWL_API_KEY),
        "Thunderbit": bool(settings.THUNDERBIT_API_KEY),
        "Browse.ai": bool(settings.BROWSEAI_API_KEY),
    }

    print(f"  FIRECRAWL_API_KEY:      {mask_api_key(settings.FIRECRAWL_API_KEY)}")
    print(f"  THUNDERBIT_API_KEY:     {mask_api_key(settings.THUNDERBIT_API_KEY)}")
    print(f"  BROWSEAI_API_KEY:      {mask_api_key(settings.BROWSEAI_API_KEY)}")
    print(f"  BROWSEAI_TEAM_ID:      {settings.BROWSEAI_TEAM_ID or '(not configured)'}")
    print(
        f"  BROWSEAI_DEFAULT_ROBOT_ID: {settings.BROWSEAI_DEFAULT_ROBOT_ID or '(not configured)'}"
    )

    return keys_status


def test_database_connection() -> bool:
    """Test database connection."""
    print_section("Database Connection")

    from pipeline.database import get_engine, check_schema_ready
    from pipeline.config import settings

    db_url_parts = settings.DATABASE_URL.split("@")
    db_host = (
        db_url_parts[-1] if "@" in settings.DATABASE_URL else settings.DATABASE_URL
    )
    print(f"  Database URL: ...@{db_host}")

    try:
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(__import__("sqlalchemy").text("SELECT 1"))
            print(f"  Connection test: SUCCESS (result: {result.scalar()})")

        schema_ready = check_schema_ready()
        if schema_ready:
            from pipeline.database import _REQUIRED_TABLES

            print(f"  Schema check: READY ({len(_REQUIRED_TABLES)} required tables)")
            return True
        else:
            print(f"  Schema check: NOT READY - run migrations")
            return False

    except Exception as e:
        print(f"  Connection test: FAILED - {str(e)}")
        return False


def test_firecrawl_scraper(topic: str, limit: int = 5) -> list[dict[str, Any]]:
    """Test Firecrawl scraper."""
    print_section(f"Firecrawl Scraper Test (topic: '{topic}')")

    from pipeline.scrapers.firecrawl_client import FirecrawlClient

    client = FirecrawlClient()

    try:
        results = client.search_indian_financial_news(topic, limit=limit)
        print(f"  Results: {len(results)} articles")

        for i, article in enumerate(results, 1):
            title = article.get("title", "No title")[:50]
            url = article.get("url", "No URL")
            source = article.get("source_name", "Unknown")
            scraper = article.get("scraper_source", "unknown")
            print(f"    {i}. {title}...")
            print(f"       URL: {url[:60]}...")
            print(f"       Source: {source} | Scraper: {scraper}")

        return results

    except Exception as e:
        print(f"  ERROR: {str(e)}")
        logger.exception("Firecrawl scraper error")
        return []


def test_thunderbit_scraper(topic: str, limit: int = 5) -> list[dict[str, Any]]:
    """Test Thunderbit scraper."""
    print_section(f"Thunderbit Scraper Test (topic: '{topic}')")

    from pipeline.scrapers.thunderbit_client import ThunderbitClient

    client = ThunderbitClient()

    try:
        results = client.search_and_scrape(topic, limit=limit)
        print(f"  Results: {len(results)} articles")

        for i, article in enumerate(results, 1):
            title = article.get("title", "No title")[:50]
            url = article.get("url", "No URL")
            source = article.get("source_name", "Unknown")
            scraper = article.get("scraper_source", "unknown")
            print(f"    {i}. {title}...")
            print(f"       URL: {url[:60]}...")
            print(f"       Source: {source} | Scraper: {scraper}")

        return results

    except Exception as e:
        print(f"  ERROR: {str(e)}")
        logger.exception("Thunderbit scraper error")
        return []


def test_browseai_scraper(topic: str) -> list[dict[str, Any]]:
    """Test Browse.ai scraper."""
    print_section(f"Browse.ai Scraper Test (topic: '{topic}')")

    from pipeline.scrapers.browseai_client import BrowseAIClient

    client = BrowseAIClient()

    try:
        results = client.search_financial_news(topic)
        print(f"  Results: {len(results)} articles")

        for i, article in enumerate(results, 1):
            title = article.get("title", "No title")[:50]
            url = article.get("url", "No URL")
            source = article.get("source_name", "Unknown")
            scraper = article.get("scraper_source", "unknown")
            print(f"    {i}. {title}...")
            print(f"       URL: {url[:60]}...")
            print(f"       Source: {source} | Scraper: {scraper}")

        return results

    except Exception as e:
        print(f"  ERROR: {str(e)}")
        logger.exception("Browse.ai scraper error")
        return []


def test_run_scrapers(topic: str, limit: int = 5) -> list[dict[str, Any]]:
    """Test the combined _run_scrapers function."""
    print_section(f"Combined _run_scrapers Test (topic: '{topic}')")

    from pipeline.tasks.extensive_research import _run_scrapers

    try:
        results = _run_scrapers(topic, limit=limit)
        print(f"  Total results: {len(results)} articles")

        scraper_counts: dict[str, int] = {}
        for article in results:
            scraper = article.get("scraper_source", "unknown")
            scraper_counts[scraper] = scraper_counts.get(scraper, 0) + 1

        print(f"  Breakdown by scraper:")
        for scraper, count in sorted(scraper_counts.items()):
            print(f"    - {scraper}: {count}")

        for i, article in enumerate(results, 1):
            title = article.get("title", "No title")[:50]
            url = article.get("url", "No URL")[:50]
            scraper = article.get("scraper_source", "unknown")
            print(f"    {i}. [{scraper}] {title}...")
            print(f"       {url}...")

        return results

    except Exception as e:
        print(f"  ERROR: {str(e)}")
        logger.exception("_run_scrapers error")
        return []


def test_store_articles(
    articles: list[dict[str, Any]], source_query: str
) -> tuple[int, list[str]]:
    """Test storing articles in the database."""
    print_section(f"Store Research Articles Test (query: '{source_query}')")

    from pipeline.tasks.extensive_research import _store_research_articles

    if not articles:
        print("  No articles to store")
        return 0, []

    print(f"  Attempting to store {len(articles)} articles...")

    try:
        new_count, article_ids = _store_research_articles(
            articles, source_query=source_query
        )
        print(f"  Stored {new_count} new articles")
        print(f"  Article IDs: {len(article_ids)} IDs generated")

        if article_ids:
            print(f"  Sample IDs:")
            for i, aid in enumerate(article_ids[:3], 1):
                print(f"    {i}. {aid}")
            if len(article_ids) > 3:
                print(f"    ... and {len(article_ids) - 3} more")

        return new_count, article_ids

    except Exception as e:
        print(f"  ERROR: {str(e)}")
        logger.exception("_store_research_articles error")
        return 0, []


def test_complete_research_flow(topic: str) -> dict[str, Any]:
    """Test the complete research_topic task flow."""
    print_section(f"Complete Research Flow Test (topic: '{topic}')")

    from pipeline.tasks.extensive_research import research_topic
    from pipeline.database import check_schema_ready

    if not check_schema_ready():
        print("  Skipping - database schema not ready")
        return {"status": "skipped", "reason": "schema_not_ready"}

    test_user_id = f"manual-test-{uuid.uuid4().hex[:8]}"
    print(f"  Using test user_id: {test_user_id}")

    try:
        print("  Running research_topic task...")
        start_time = datetime.now()

        result = research_topic.apply(args=[topic, test_user_id])

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        print(f"  Task status: {result.status}")
        print(f"  Duration: {duration:.2f} seconds")

        if result.status == "SUCCESS":
            data = result.result
            print(f"  Results:")
            print(f"    - Status: {data.get('status')}")
            print(f"    - Topic: {data.get('topic')}")
            print(f"    - New articles: {data.get('new_articles')}")
            print(f"    - Total found: {data.get('total_found')}")
            print(f"    - Query count: {data.get('query_count')}")
            print(f"    - Article IDs: {len(data.get('article_ids', []))}")

            return {
                "status": "success",
                "new_articles": data.get("new_articles"),
                "total_found": data.get("total_found"),
                "duration": duration,
            }
        else:
            print(f"  Task failed: {result.result}")
            return {
                "status": "failed",
                "error": str(result.result),
                "duration": duration,
            }

    except Exception as e:
        print(f"  ERROR: {str(e)}")
        logger.exception("Complete research flow error")
        return {"status": "error", "error": str(e)}


def print_summary(
    api_keys: dict[str, bool],
    db_ready: bool,
    firecrawl_results: list,
    thunderbit_results: list,
    browseai_results: list,
    combined_results: list,
    store_results: tuple,
    flow_results: dict,
) -> None:
    """Print a summary of all test results."""
    print_header("TEST SUMMARY")

    print(f"API Keys Configured:")
    for service, configured in api_keys.items():
        status = "YES" if configured else "NO"
        print(f"  - {service}: {status}")

    print(f"\nDatabase:")
    print(f"  - Connection: {'OK' if db_ready else 'FAILED'}")
    print(f"  - Schema: {'Ready' if db_ready else 'Not Ready'}")

    print(f"\nScraper Results:")
    print(f"  - Firecrawl: {len(firecrawl_results)} articles")
    print(f"  - Thunderbit: {len(thunderbit_results)} articles")
    print(f"  - Browse.ai: {len(browseai_results)} articles")
    print(f"  - Combined: {len(combined_results)} articles")

    print(f"\nStorage Results:")
    print(f"  - Stored: {store_results[0]} new articles")

    print(f"\nComplete Flow:")
    print(f"  - Status: {flow_results.get('status')}")
    if flow_results.get("status") == "success":
        print(f"  - New articles: {flow_results.get('new_articles')}")
        print(f"  - Total found: {flow_results.get('total_found')}")
        print(f"  - Duration: {flow_results.get('duration'):.2f}s")
    elif flow_results.get("status") == "skipped":
        print(f"  - Reason: {flow_results.get('reason')}")
    else:
        print(f"  - Error: {flow_results.get('error')}")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Test deep research functionality")
    parser.add_argument(
        "--topic",
        type=str,
        default="iran",
        help="Topic to research (default: 'iran')",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Limit number of results per scraper (default: 5)",
    )
    parser.add_argument(
        "--skip-scrapers",
        action="store_true",
        help="Skip individual scraper tests",
    )
    parser.add_argument(
        "--skip-flow",
        action="store_true",
        help="Skip complete flow test",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    topic = args.topic
    limit = args.limit

    print_header(f"Deep Research Debug Script")
    print(f"Topic: {topic}")
    print(f"Limit: {limit} results per scraper")

    api_keys = print_api_keys()

    db_ready = test_database_connection()

    firecrawl_results = []
    thunderbit_results = []
    browseai_results = []
    combined_results = []

    if not args.skip_scrapers:
        if api_keys.get("Firecrawl"):
            firecrawl_results = test_firecrawl_scraper(topic, limit)
        else:
            print_section("Firecrawl Skipped (not configured)")
            print("  Skipping - API key not configured")

        if api_keys.get("Thunderbit"):
            thunderbit_results = test_thunderbit_scraper(topic, limit)
        else:
            print_section("Thunderbit Skipped (not configured)")
            print("  Skipping - API key not configured")

        if api_keys.get("Browse.ai"):
            browseai_results = test_browseai_scraper(topic)
        else:
            print_section("Browse.ai Skipped (not configured)")
            print("  Skipping - API key not configured")

        combined_results = test_run_scrapers(topic, limit)

        if combined_results and db_ready:
            store_results = test_store_articles(combined_results[:3], f"test {topic}")
        else:
            print_section("Store Articles")
            if not combined_results:
                print("  Skipping - no articles to store")
            else:
                print("  Skipping - database not ready")
            store_results = (0, [])
    else:
        print_section("Individual Scraper Tests Skipped")
        store_results = (0, [])

    flow_results = {"status": "skipped", "reason": "explicitly_skipped"}
    if not args.skip_flow:
        flow_results = test_complete_research_flow(topic)
    else:
        print_section("Complete Flow Test Skipped")

    print_summary(
        api_keys,
        db_ready,
        firecrawl_results,
        thunderbit_results,
        browseai_results,
        combined_results,
        store_results,
        flow_results,
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
