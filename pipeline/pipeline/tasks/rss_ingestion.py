"""RSS feed ingestion task for Indian financial news sources."""

import logging
from datetime import datetime, timezone

from pipeline.celery_app import app
from pipeline.database import get_db
from pipeline.scrapers.rss_feeds import RSSFeedParser
from pipeline.utils.deduplication import compute_content_hash
from pipeline.utils.text_cleaner import clean_html
from sqlalchemy import text

logger = logging.getLogger(__name__)

# Indian financial news RSS feed sources
FEED_SOURCES: dict[str, list[str]] = {
    "MoneyControl": [
        "https://www.moneycontrol.com/rss/latestnews.xml",
        "https://www.moneycontrol.com/rss/marketreports.xml",
    ],
    "Economic Times": [
        "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
        "https://economictimes.indiatimes.com/news/economy/rssfeeds/1373380680.cms",
    ],
    "LiveMint": [
        "https://www.livemint.com/rss/markets",
        "https://www.livemint.com/rss/money",
    ],
    "Business Standard": [
        "https://www.business-standard.com/rss/markets-106.rss",
        "https://www.business-standard.com/rss/economy-102.rss",
    ],
    "CNBC TV18": [
        "https://www.cnbctv18.com/commonfeeds/v1/cne/rss/market.xml",
    ],
    "NDTV Profit": [
        "https://feeds.feedburner.com/ndtvprofit-latest",
    ],
}


@app.task(name="pipeline.tasks.rss_ingestion.fetch_all_feeds")
def fetch_all_feeds() -> dict:
    """Fetch articles from all configured RSS feeds.

    Iterates through all feed sources and dispatches individual
    feed fetch tasks for parallel processing.
    """
    logger.info("Starting RSS ingestion for all feeds")
    results = {}
    for source_name, feed_urls in FEED_SOURCES.items():
        for feed_url in feed_urls:
            logger.info("Dispatching fetch for %s: %s", source_name, feed_url)
            fetch_single_feed.delay(feed_url, source_name)
            results[feed_url] = "dispatched"
    logger.info("Dispatched %d feed fetch tasks", len(results))
    return results


@app.task(name="pipeline.tasks.rss_ingestion.fetch_single_feed")
def fetch_single_feed(feed_url: str, source_name: str) -> dict:
    """Fetch and parse a single RSS feed.

    Args:
        feed_url: URL of the RSS feed to fetch.
        source_name: Human-readable name of the news source.

    Returns:
        Dict with feed URL, source name, and count of articles fetched.
    """
    from pipeline.tasks.web_scraper import scrape_article

    logger.info("Fetching feed: %s (%s)", feed_url, source_name)
    parser = RSSFeedParser()
    entries = parser.fetch_feed(feed_url)
    new_articles_count = 0

    with get_db() as db:
        for entry in entries:
            url = entry.get("link", "")
            if not url:
                continue

            existing = db.execute(
                text("SELECT id FROM news_articles WHERE url = :url"), {"url": url}
            ).fetchone()

            if existing:
                continue

            title = entry.get("title", "")
            summary_raw = entry.get("summary", "")
            summary = clean_html(summary_raw) if summary_raw else None
            published_raw = entry.get("published")
            if published_raw:
                try:
                    published_at = datetime.fromisoformat(
                        published_raw.replace("Z", "+00:00")
                    )
                except ValueError:
                    published_at = datetime.now(timezone.utc)
            else:
                published_at = datetime.now(timezone.utc)

            content_hash = compute_content_hash(title + (summary or ""))

            result = db.execute(
                text("""
                    INSERT INTO news_articles 
                    (title, summary, url, source, published_at, content_hash, category)
                    VALUES (:title, :summary, :url, :source, :published_at, :content_hash, :category)
                    RETURNING id
                """),
                {
                    "title": title,
                    "summary": summary,
                    "url": url,
                    "source": source_name,
                    "published_at": published_at,
                    "content_hash": content_hash,
                    "category": None,
                },
            )
            article_id = result.scalar()
            new_articles_count += 1

            try:
                from pipeline.utils.publisher import publish_new_article

                publish_new_article(
                    article_id=str(article_id),
                    title=title,
                    source=source_name,
                    url=url,
                    published_at=published_at.isoformat() if published_at else None,
                )
            except Exception:
                pass

            if article_id:
                scrape_article.delay(str(article_id), url)

    logger.info(
        "Feed fetch complete: %s - %d new articles", feed_url, new_articles_count
    )
    return {
        "feed_url": feed_url,
        "source": source_name,
        "articles_fetched": new_articles_count,
    }
