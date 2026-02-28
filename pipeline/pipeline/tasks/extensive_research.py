"""Extensive research tasks using Firecrawl, Thunderbit, and Browse.ai scrapers.

Orchestrates all three scraping services to perform deep research on a
stock, topic, or entire portfolio.  Results are deduplicated by URL,
stored in ``news_articles``, and downstream analysis tasks are dispatched
automatically.
"""

import logging
import uuid
from datetime import datetime, UTC

from celery import Task
from sqlalchemy import text

from pipeline.celery_app import app
from pipeline.database import get_db
from pipeline.config import settings
from pipeline.utils.deduplication import compute_content_hash
from pipeline.utils.publisher import publish_event

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper: store deduplicated research articles
# ---------------------------------------------------------------------------


def _store_research_articles(articles: list[dict], source_query: str) -> int:
    """Persist scraped articles into ``news_articles`` after URL deduplication.

    Args:
        articles: Normalised article dicts from any scraper.  Expected keys:
            ``title``, ``url``, ``content``, ``source_name``, ``published_at``.
        source_query: The search query that produced these results.

    Returns:
        Number of newly inserted articles.
    """
    if not articles:
        return 0

    new_count = 0

    try:
        with get_db() as db:
            for article in articles:
                url = (article.get("url") or "").strip()
                if not url:
                    continue

                # --- URL deduplication --------------------------------
                existing = db.execute(
                    text("SELECT id FROM news_articles WHERE url = :url"),
                    {"url": url},
                ).fetchone()

                if existing:
                    logger.debug("Duplicate URL skipped: %s", url)
                    continue

                # --- Prepare fields -----------------------------------
                title = (article.get("title") or "")[:500]
                content = article.get("content") or ""
                source_name = (article.get("source_name") or "")[:100]
                published_at = article.get("published_at")

                if isinstance(published_at, str) and published_at:
                    try:
                        published_at = datetime.fromisoformat(
                            published_at.replace("Z", "+00:00")
                        )
                    except (ValueError, TypeError):
                        published_at = None

                article_id = str(uuid.uuid4())
                now = datetime.now(UTC)

                db.execute(
                    text("""
                        INSERT INTO news_articles
                            (id, title, url, source, published_at,
                             scraped_at, full_text, source_query)
                        VALUES
                            (:id, :title, :url, :source, :published_at,
                             :scraped_at, :full_text, :source_query)
                    """),
                    {
                        "id": article_id,
                        "title": title,
                        "url": url,
                        "source": source_name,
                        "published_at": published_at,
                        "scraped_at": now,
                        "full_text": content,
                        "source_query": source_query,
                    },
                )
                new_count += 1

                # Dispatch downstream analysis tasks for every new article
                try:
                    from pipeline.tasks.sentiment_analysis import analyze_article

                    analyze_article.delay(article_id)
                except Exception:
                    logger.warning(
                        "Failed to dispatch sentiment analysis for %s", article_id
                    )

                try:
                    from pipeline.tasks.ticker_identification import identify_tickers

                    identify_tickers.delay(article_id)
                except Exception:
                    logger.warning(
                        "Failed to dispatch ticker identification for %s", article_id
                    )

    except Exception:
        logger.error(
            "Error storing research articles for query '%s'",
            source_query,
            exc_info=True,
        )

    logger.info(
        "Stored %d new articles (of %d total) for query: %s",
        new_count,
        len(articles),
        source_query,
    )
    return new_count


# ---------------------------------------------------------------------------
# Helper: run all three scrapers for a single query
# ---------------------------------------------------------------------------


def _run_scrapers(query: str, limit: int = 10) -> list[dict]:
    """Execute Firecrawl, Thunderbit, and Browse.ai searches sequentially.

    Firecrawl is tried first (most reliable), then Thunderbit, then
    Browse.ai as a fallback.  Results from all services are merged.

    Args:
        query: Search query string.
        limit: Per-service result limit.

    Returns:
        Combined list of normalised article dicts.
    """
    all_articles: list[dict] = []

    # 1. Firecrawl (primary) -------------------------------------------
    try:
        from pipeline.scrapers.firecrawl_client import FirecrawlClient

        fc = FirecrawlClient()
        fc_results = fc.search_indian_financial_news(query, limit=limit)
        all_articles.extend(fc_results)
        logger.info("Firecrawl returned %d results for: %s", len(fc_results), query)
    except Exception:
        logger.warning("Firecrawl scraper failed for query: %s", query, exc_info=True)

    # 2. Thunderbit (secondary) ----------------------------------------
    try:
        from pipeline.scrapers.thunderbit_client import ThunderbitClient

        tb = ThunderbitClient()
        tb_results = tb.search_and_scrape(query, limit=limit)
        all_articles.extend(tb_results)
        logger.info("Thunderbit returned %d results for: %s", len(tb_results), query)
    except Exception:
        logger.warning("Thunderbit scraper failed for query: %s", query, exc_info=True)

    # 3. Browse.ai (fallback) ------------------------------------------
    try:
        from pipeline.scrapers.browseai_client import BrowseAIClient

        ba = BrowseAIClient()
        ba_results = ba.search_financial_news(query)
        all_articles.extend(ba_results)
        logger.info("Browse.ai returned %d results for: %s", len(ba_results), query)
    except Exception:
        logger.warning("Browse.ai scraper failed for query: %s", query, exc_info=True)

    return all_articles


# ---------------------------------------------------------------------------
# Celery tasks
# ---------------------------------------------------------------------------


@app.task(
    name="pipeline.tasks.extensive_research.research_stock",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def research_stock(self: Task, ticker: str, user_id: str) -> dict:
    """Perform deep research on a single stock using all scraping services.

    Builds several search queries around the ticker / company name, runs
    all three scrapers for each query, deduplicates by URL, stores new
    articles, and dispatches downstream analysis tasks.

    Args:
        ticker: NSE/BSE ticker symbol (e.g. ``"RELIANCE"``).
        user_id: ID of the user who initiated the research.

    Returns:
        Dict summarising results including status, new article count, etc.
    """
    logger.info(
        "Starting extensive stock research: ticker=%s, user=%s", ticker, user_id
    )

    self.update_state(
        state="PROGRESS",
        meta={"stage": "building_queries", "ticker": ticker},
    )

    # Build a set of search queries to maximise coverage
    queries = [
        f"{ticker} stock news",
        f"{ticker} NSE BSE India",
        f"{ticker} quarterly results analysis",
        f"{ticker} share price target",
    ]

    # Attempt to look up the company name for richer queries
    company_name = None
    try:
        with get_db() as db:
            row = db.execute(
                text("SELECT company_name FROM stocks WHERE ticker = :ticker"),
                {"ticker": ticker},
            ).fetchone()
            if row:
                company_name = row.company_name
    except Exception:
        logger.debug("Could not resolve company name for ticker %s", ticker)

    if company_name:
        queries.insert(0, f"{company_name} stock news")
        queries.append(f"{company_name} financial results India")

    total_found = 0
    total_new = 0

    for idx, query in enumerate(queries, start=1):
        self.update_state(
            state="PROGRESS",
            meta={
                "stage": "scraping",
                "ticker": ticker,
                "query": query,
                "query_index": idx,
                "total_queries": len(queries),
            },
        )

        try:
            articles = _run_scrapers(query, limit=10)
            total_found += len(articles)
            new = _store_research_articles(articles, source_query=query)
            total_new += new
        except Exception:
            logger.error(
                "Error during research_stock scraping (query=%s)",
                query,
                exc_info=True,
            )

    # Publish completion event
    try:
        publish_event(
            "research",
            {
                "type": "stock_research_complete",
                "ticker": ticker,
                "user_id": user_id,
                "articles_found": total_new,
            },
        )
    except Exception:
        logger.warning("Failed to publish research completion event for %s", ticker)

    logger.info(
        "Stock research complete: ticker=%s, new=%d, total_found=%d",
        ticker,
        total_new,
        total_found,
    )

    return {
        "status": "completed",
        "ticker": ticker,
        "new_articles": total_new,
        "total_found": total_found,
    }


@app.task(
    name="pipeline.tasks.extensive_research.research_topic",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def research_topic(self: Task, topic: str, user_id: str) -> dict:
    """Perform deep research on an arbitrary topic.

    Uses the topic directly as the search query across all three scraping
    services.

    Args:
        topic: Free-text topic/query string.
        user_id: ID of the user who initiated the research.

    Returns:
        Dict summarising results.
    """
    logger.info(
        "Starting extensive topic research: topic='%s', user=%s", topic, user_id
    )

    self.update_state(
        state="PROGRESS",
        meta={"stage": "building_queries", "topic": topic},
    )

    queries = [
        topic,
        f"{topic} India stock market",
        f"{topic} financial impact analysis",
    ]

    total_found = 0
    total_new = 0

    for idx, query in enumerate(queries, start=1):
        self.update_state(
            state="PROGRESS",
            meta={
                "stage": "scraping",
                "topic": topic,
                "query": query,
                "query_index": idx,
                "total_queries": len(queries),
            },
        )

        try:
            articles = _run_scrapers(query, limit=10)
            total_found += len(articles)
            new = _store_research_articles(articles, source_query=query)
            total_new += new
        except Exception:
            logger.error(
                "Error during research_topic scraping (query=%s)",
                query,
                exc_info=True,
            )

    # Publish completion event
    try:
        publish_event(
            "research",
            {
                "type": "topic_research_complete",
                "topic": topic,
                "user_id": user_id,
                "articles_found": total_new,
            },
        )
    except Exception:
        logger.warning(
            "Failed to publish research completion event for topic '%s'", topic
        )

    logger.info(
        "Topic research complete: topic='%s', new=%d, total_found=%d",
        topic,
        total_new,
        total_found,
    )

    return {
        "status": "completed",
        "topic": topic,
        "new_articles": total_new,
        "total_found": total_found,
    }


@app.task(
    name="pipeline.tasks.extensive_research.research_portfolio",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def research_portfolio(self: Task, portfolio_id: str, user_id: str) -> dict:
    """Fan-out extensive research for every stock in a portfolio.

    Looks up the portfolio's constituent stocks from the database and
    dispatches an individual :func:`research_stock` task for each one.

    Args:
        portfolio_id: Database ID of the portfolio.
        user_id: ID of the user who initiated the research.

    Returns:
        Dict with dispatch status and stock count.
    """
    logger.info(
        "Starting portfolio research: portfolio=%s, user=%s", portfolio_id, user_id
    )

    self.update_state(
        state="PROGRESS",
        meta={"stage": "loading_portfolio", "portfolio_id": portfolio_id},
    )

    tickers: list[str] = []
    try:
        with get_db() as db:
            rows = db.execute(
                text("""
                    SELECT s.ticker
                    FROM portfolio_stocks ps
                    JOIN stocks s ON s.id = ps.stock_id
                    WHERE ps.portfolio_id = :portfolio_id
                """),
                {"portfolio_id": portfolio_id},
            ).fetchall()
            tickers = [row.ticker for row in rows]
    except Exception:
        logger.error(
            "Failed to load portfolio stocks for %s", portfolio_id, exc_info=True
        )
        return {
            "status": "error",
            "portfolio_id": portfolio_id,
            "stocks_count": 0,
            "error": "Failed to load portfolio stocks",
        }

    if not tickers:
        logger.warning("No stocks found for portfolio %s", portfolio_id)
        return {
            "status": "completed",
            "portfolio_id": portfolio_id,
            "stocks_count": 0,
        }

    self.update_state(
        state="PROGRESS",
        meta={
            "stage": "dispatching",
            "portfolio_id": portfolio_id,
            "stocks_count": len(tickers),
        },
    )

    dispatched = 0
    for ticker in tickers:
        try:
            research_stock.delay(ticker, user_id)
            dispatched += 1
        except Exception:
            logger.error(
                "Failed to dispatch research for ticker %s (portfolio %s)",
                ticker,
                portfolio_id,
                exc_info=True,
            )

    # Publish completion event
    try:
        publish_event(
            "research",
            {
                "type": "portfolio_research_dispatched",
                "portfolio_id": portfolio_id,
                "user_id": user_id,
                "stocks_count": dispatched,
            },
        )
    except Exception:
        logger.warning(
            "Failed to publish portfolio research event for %s", portfolio_id
        )

    logger.info(
        "Portfolio research dispatched: portfolio=%s, stocks=%d",
        portfolio_id,
        dispatched,
    )

    return {
        "status": "dispatched",
        "portfolio_id": portfolio_id,
        "stocks_count": dispatched,
    }
