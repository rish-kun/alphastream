"""Google News scraping task for Indian financial news.

Searches Google News for stock-related queries, stores new articles
in the database, and dispatches sentiment analysis tasks.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from celery import Task
from sqlalchemy import text

from pipeline.celery_app import app
from pipeline.database import check_schema_ready, get_db
from pipeline.scrapers.article_scraper import ArticleScraper
from pipeline.utils.deduplication import compute_content_hash
from pipeline.utils.publisher import publish_event

logger = logging.getLogger(__name__)

DEFAULT_STOCK_LIMIT = 50


def _get_nse_tickers(limit: int = DEFAULT_STOCK_LIMIT) -> list[str]:
    """Fetch top NSE stock tickers from database ordered by market cap."""
    try:
        with get_db() as db:
            result = db.execute(
                text("""
                    SELECT ticker FROM stocks
                    WHERE exchange = 'NSE'
                    ORDER BY market_cap DESC NULLS LAST
                    LIMIT :limit
                """),
                {"limit": limit},
            )
            rows = result.fetchall()
            return [row.ticker for row in rows]
    except Exception:
        logger.warning("Failed to fetch NSE tickers from database")
        return []


def _check_url_exists(db: Any, url: str) -> bool:
    """Check if article URL already exists in database."""
    result = db.execute(
        text("SELECT id FROM news_articles WHERE url = :url"),
        {"url": url},
    )
    return result.fetchone() is not None


def _check_content_hash_exists(db: Any, content_hash: str) -> bool:
    """Check if article content hash already exists in database."""
    result = db.execute(
        text("SELECT id FROM news_articles WHERE content_hash = :content_hash"),
        {"content_hash": content_hash},
    )
    return result.fetchone() is not None


def _store_article(
    db: Any,
    article: dict,
    source_query: str,
) -> str | None:
    """Store a single article in the database after deduplication.

    Args:
        db: Database session.
        article: Article dict with keys: title, url, content, source_name, published_at.
        source_query: The search query that produced this article.

    Returns:
        Article ID if stored, None if duplicate or failed.
    """
    url = (article.get("url") or "").strip()
    if not url:
        return None

    if _check_url_exists(db, url):
        logger.debug("Duplicate URL skipped: %s", url)
        return None

    title = (article.get("title") or "")[:500]
    content = article.get("content") or ""
    source_name = (article.get("source_name") or "Google News")[:100]
    published_at = article.get("published_at")

    if isinstance(published_at, str) and published_at:
        try:
            published_at = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            published_at = datetime.now(timezone.utc)
    elif not isinstance(published_at, datetime):
        published_at = datetime.now(timezone.utc)

    article_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    summary = content[:400] if content else None
    content_hash = compute_content_hash(f"{title}|{content}|{url}")

    if _check_content_hash_exists(db, content_hash):
        logger.debug("Duplicate content hash skipped: %s", content_hash)
        return None

    try:
        db.execute(
            text("""
                INSERT INTO news_articles
                    (id, title, summary, url, source, published_at,
                     scraped_at, full_text, content_hash, category)
                VALUES
                    (:id, :title, :summary, :url, :source, :published_at,
                     :scraped_at, :full_text, :content_hash, :category)
            """),
            {
                "id": article_id,
                "title": title,
                "summary": summary,
                "url": url,
                "source": source_name[:50],
                "published_at": published_at,
                "scraped_at": now,
                "full_text": content,
                "content_hash": content_hash,
                "category": "google_news",
            },
        )
        return article_id
    except Exception as e:
        logger.error("Failed to store article %s: %s", url, e)
        return None


def _scrape_article_content(url: str) -> str | None:
    """Scrape full content from article URL using ArticleScraper."""
    try:
        scraper = ArticleScraper()
        return scraper.scrape(url)
    except Exception as e:
        logger.warning("Failed to scrape article content for %s: %s", url, e)
        return None


def _dispatch_sentiment_analysis(article_id: str) -> None:
    """Dispatch sentiment analysis task for an article."""
    try:
        from pipeline.tasks.sentiment_analysis import analyze_article

        analyze_article.delay(article_id)
    except Exception as e:
        logger.warning(
            "Failed to dispatch sentiment analysis for %s: %s", article_id, e
        )


def _search_google_news(query: str, limit: int = 10) -> list[dict]:
    """Search Google News for a query and return article results."""
    try:
        from pipeline.scrapers.google_news import GoogleNewsClient

        client = GoogleNewsClient()
        return client.search(query, limit=limit)
    except ImportError:
        logger.error(
            "GoogleNewsClient not found. Install google-news-google-custom-search or implement client."
        )
        return []
    except Exception as e:
        logger.warning("Google News search failed for query '%s': %s", query, e)
        return []


@app.task(
    name="pipeline.tasks.google_news_scraper.scrape_google_news",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def scrape_google_news(self: Task, stock_tickers: list[str] | None = None) -> dict:
    """Scrape Google News for given stock tickers.

    If no tickers provided, fetches top NSE stocks from database.
    For each ticker, searches Google News and stores new articles.

    Args:
        stock_tickers: Optional list of stock ticker symbols (e.g., ["TCS", "RELIANCE"]).
                      If None, fetches top NSE stocks from database.

    Returns:
        Dict with status, counts, and processed tickers.
    """
    if not check_schema_ready():
        return {"status": "skipped", "reason": "database schema not ready"}

    if stock_tickers is None:
        stock_tickers = _get_nse_tickers(limit=DEFAULT_STOCK_LIMIT)

    if not stock_tickers:
        return {"status": "error", "reason": "no stock tickers available"}

    logger.info(
        "Starting Google News scraping for %d tickers",
        len(stock_tickers),
    )

    total_found = 0
    total_new = 0
    failed_tickers: list[str] = []
    new_article_ids: list[str] = []

    for idx, ticker in enumerate(stock_tickers, start=1):
        query = f"{ticker} stock"

        self.update_state(
            state="PROGRESS",
            meta={
                "current_stock": ticker,
                "query": query,
                "processed": idx - 1,
                "total": len(stock_tickers),
                "new_articles": total_new,
            },
        )

        try:
            articles = _search_google_news(query, limit=10)
            total_found += len(articles)

            with get_db() as db:
                for article in articles:
                    article_id = _store_article(db, article, source_query=query)
                    if article_id:
                        new_article_ids.append(article_id)
                        total_new += 1
                        full_content = _scrape_article_content(article.get("url", ""))
                        if full_content:
                            try:
                                db.execute(
                                    text("""
                                        UPDATE news_articles
                                        SET full_text = :full_text
                                        WHERE id = :id
                                    """),
                                    {"full_text": full_content, "id": article_id},
                                )
                            except Exception as e:
                                logger.warning(
                                    "Failed to update full_text for %s: %s",
                                    article_id,
                                    e,
                                )

            for article_id in new_article_ids[-total_new:]:
                _dispatch_sentiment_analysis(article_id)

        except Exception as e:
            logger.error(
                "Error processing ticker %s: %s",
                ticker,
                e,
                exc_info=True,
            )
            failed_tickers.append(ticker)
            continue

        self.update_state(
            state="PROGRESS",
            meta={
                "current_stock": ticker,
                "query": query,
                "processed": idx,
                "total": len(stock_tickers),
                "new_articles": total_new,
            },
        )

    logger.info(
        "Google News scraping complete: new=%d, found=%d, failed=%d",
        total_new,
        total_found,
        len(failed_tickers),
    )

    return {
        "status": "completed",
        "tickers_processed": len(stock_tickers) - len(failed_tickers),
        "tickers_failed": len(failed_tickers),
        "failed_tickers": failed_tickers,
        "articles_found": total_found,
        "articles_new": total_new,
        "article_ids": new_article_ids,
    }


@app.task(
    name="pipeline.tasks.google_news_scraper.scrape_single_ticker",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def scrape_single_ticker(self: Task, ticker: str) -> dict:
    """Scrape Google News for a single stock ticker.

    Convenience task for scraping news for one stock.

    Args:
        ticker: Stock ticker symbol (e.g., "TCS", "RELIANCE").

    Returns:
        Dict with status and article counts.
    """
    logger.info("Scraping Google News for single ticker: %s", ticker)

    return scrape_google_news.delay(stock_tickers=[ticker])


@app.task(
    name="pipeline.tasks.google_news_scraper.scrape_google_news_by_keyword",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def scrape_google_news_by_keyword(
    self: Task,
    keyword: str,
    user_id: str | None = None,
    max_results: int = 30,
) -> dict:
    """Scrape Google News for a specific keyword/topic.

    Triggered when user searches for keywords in news search.

    Args:
        keyword: The search keyword/topic
        user_id: Optional user ID who triggered the search (for tracking)
        max_results: Maximum articles to fetch (default 30)

    Returns:
        dict with status, articles found, new articles stored, etc.
    """
    if not check_schema_ready():
        return {"status": "skipped", "reason": "database schema not ready"}

    if not keyword or not keyword.strip():
        return {"status": "error", "reason": "keyword cannot be empty"}

    keyword = keyword.strip()
    logger.info(
        "Starting Google News scraping for keyword: %s (max_results=%d)",
        keyword,
        max_results,
    )

    self.update_state(
        state="PROGRESS",
        meta={
            "status": "search_initiated",
            "keyword": keyword,
            "user_id": user_id,
        },
    )

    try:
        from pipeline.scrapers.google_news import GoogleNewsClient

        client = GoogleNewsClient()
        articles = client.search(keyword, max_results=max_results)
    except Exception as e:
        logger.error("Failed to search Google News for keyword '%s': %s", keyword, e)
        return {
            "status": "error",
            "keyword": keyword,
            "reason": f"search failed: {str(e)}",
        }

    self.update_state(
        state="PROGRESS",
        meta={
            "status": "articles_found",
            "keyword": keyword,
            "articles_found": len(articles),
            "user_id": user_id,
        },
    )

    logger.info("Found %d articles for keyword: %s", len(articles), keyword)

    new_article_ids: list[str] = []
    failed_count = 0
    processed_count = 0

    for idx, article in enumerate(articles, start=1):
        url = (article.get("url") or "").strip()
        if not url:
            failed_count += 1
            continue

        self.update_state(
            state="PROGRESS",
            meta={
                "status": "processing",
                "keyword": keyword,
                "processed": idx,
                "total": len(articles),
                "new_articles": len(new_article_ids),
                "current_url": url[:50],
            },
        )

        try:
            with get_db() as db:
                if _check_url_exists(db, url):
                    logger.debug("Duplicate URL skipped: %s", url)
                    processed_count += 1
                    continue

                full_content = _scrape_article_content(url)
                if not full_content:
                    logger.warning("Failed to scrape content for: %s", url)
                    full_content = article.get("content") or ""

                title = (article.get("title") or "")[:500]
                content_hash = compute_content_hash(f"{title}|{full_content}|{url}")

                if _check_content_hash_exists(db, content_hash):
                    logger.debug("Duplicate content hash skipped: %s", content_hash)
                    processed_count += 1
                    continue

                source_name = (article.get("source_name") or "Google News")[:100]
                published_at = article.get("published_at")

                if isinstance(published_at, str) and published_at:
                    try:
                        published_at = datetime.fromisoformat(
                            published_at.replace("Z", "+00:00")
                        )
                    except (ValueError, TypeError):
                        published_at = datetime.now(timezone.utc)
                elif not isinstance(published_at, datetime):
                    published_at = datetime.now(timezone.utc)

                article_id = str(uuid.uuid4())
                now = datetime.now(timezone.utc)
                summary = full_content[:400] if full_content else None

                db.execute(
                    text("""
                        INSERT INTO news_articles
                            (id, title, summary, url, source, published_at,
                             scraped_at, full_text, content_hash, category)
                        VALUES
                            (:id, :title, :summary, :url, :source, :published_at,
                             :scraped_at, :full_text, :content_hash, :category)
                    """),
                    {
                        "id": article_id,
                        "title": title,
                        "summary": summary,
                        "url": url,
                        "source": source_name[:50],
                        "published_at": published_at,
                        "scraped_at": now,
                        "full_text": full_content,
                        "content_hash": content_hash,
                        "category": "keyword_search",
                    },
                )

                new_article_ids.append(article_id)
                processed_count += 1

                _dispatch_sentiment_analysis(article_id)

        except Exception as e:
            logger.error(
                "Failed to process article %s: %s",
                url,
                e,
                exc_info=True,
            )
            failed_count += 1
            continue

    logger.info(
        "Keyword search complete: keyword=%s, found=%d, new=%d, failed=%d",
        keyword,
        len(articles),
        len(new_article_ids),
        failed_count,
    )

    publish_event(
        "feed",
        {
            "type": "keyword_search_complete",
            "keyword": keyword,
            "articles_found": len(articles),
            "new_articles": len(new_article_ids),
            "user_id": user_id,
        },
    )

    return {
        "status": "success",
        "keyword": keyword,
        "articles_found": len(articles),
        "new_articles": len(new_article_ids),
        "failed_scrapes": failed_count,
        "article_ids": [str(id) for id in new_article_ids],
    }
