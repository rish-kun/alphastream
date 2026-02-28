"""Full-text web scraping task for article content extraction."""

import logging

from pipeline.celery_app import app
from pipeline.database import check_schema_ready, get_db
from pipeline.scrapers.article_scraper import ArticleScraper
from pipeline.utils.text_cleaner import clean_article_text
from sqlalchemy import text

logger = logging.getLogger(__name__)


@app.task(name="pipeline.tasks.web_scraper.scrape_pending_articles")
def scrape_pending_articles() -> dict:
    """Scrape full text for all articles pending content extraction.

    Queries the database for articles without full text content and
    dispatches individual scrape tasks for each.
    """
    if not check_schema_ready():
        return {"status": "skipped", "reason": "database schema not ready"}

    logger.info("Starting full-text scrape for pending articles")

    with get_db() as db:
        rows = db.execute(
            text("SELECT id, url FROM news_articles WHERE full_text IS NULL LIMIT 50")
        ).fetchall()

    dispatched = 0
    for row in rows:
        scrape_article.delay(str(row.id), row.url)
        dispatched += 1

    logger.info(
        "Full-text scrape dispatch complete: %d articles dispatched", dispatched
    )
    return {"articles_dispatched": dispatched}


@app.task(
    name="pipeline.tasks.web_scraper.scrape_article",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def scrape_article(self, article_id: str, url: str) -> dict:
    """Scrape full text content from a single article URL.

    Args:
        article_id: Database ID of the article record.
        url: URL of the article to scrape.

    Returns:
        Dict with article ID, URL, and extraction status.
    """
    from pipeline.tasks.sentiment_analysis import analyze_article as sentiment_task
    from pipeline.tasks.ticker_identification import identify_tickers as ticker_task

    logger.info("Scraping article %s: %s", article_id, url)

    try:
        scraper = ArticleScraper()
        scraped_text = scraper.scrape(url)

        if scraped_text is None:
            logger.warning("Failed to extract text from %s", url)
            return {
                "article_id": article_id,
                "url": url,
                "status": "failed",
                "error": "no text extracted",
            }

        cleaned_text = clean_article_text(scraped_text)

        with get_db() as db:
            db.execute(
                text("UPDATE news_articles SET full_text = :full_text WHERE id = :id"),
                {"full_text": cleaned_text, "id": article_id},
            )

        sentiment_task.delay(article_id)
        ticker_task.delay(article_id)

        logger.info("Article scrape complete: %s", article_id)
        return {"article_id": article_id, "url": url, "status": "success"}

    except Exception as exc:
        logger.warning("Error scraping article %s: %s", article_id, exc)
        raise self.retry(exc=exc)
