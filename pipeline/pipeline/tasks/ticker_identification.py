"""Ticker identification task using NER and ticker resolution."""

import logging
import re
from typing import Optional

from celery import Task
from sqlalchemy import text

from pipeline.celery_app import app
from pipeline.database import get_db

logger = logging.getLogger(__name__)

TICKER_PATTERN = re.compile(r"\$([A-Z]{2,5})|NSE:([A-Z]{2,5})")


@app.task(name="pipeline.tasks.ticker_identification.identify_tickers_pending")
def identify_tickers_pending() -> dict:
    """Identify stock tickers in all articles pending NER processing.

    Queries the database for articles that have not yet been processed
    for named entity recognition and ticker resolution.
    """
    logger.info("Starting ticker identification for pending articles")

    with get_db() as db:
        result = db.execute(
            text("""
                SELECT na.id FROM news_articles na
                WHERE na.full_text IS NOT NULL
                AND na.id NOT IN (SELECT DISTINCT article_id FROM article_stock_mentions)
                LIMIT 50
            """),
        )
        rows = result.fetchall()

    count = 0
    for row in rows:
        article_id = str(row.id)
        identify_tickers.delay(article_id)
        count += 1

    logger.info(
        "Ticker identification dispatch complete: %d articles dispatched", count
    )
    return {"articles_dispatched": count}


@app.task(
    name="pipeline.tasks.ticker_identification.identify_tickers",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
)
def identify_tickers(self: Task, article_id: str) -> dict:
    """Identify and resolve stock tickers mentioned in an article.

    Uses NER to extract organization entities, then resolves them
    to NSE ticker symbols using the ticker alias dictionary.

    Args:
        article_id: Database ID of the article to process.

    Returns:
        Dict with article ID and list of resolved tickers.
    """
    logger.info("Identifying tickers for article: %s", article_id)

    with get_db() as db:
        result = db.execute(
            text("SELECT title, full_text FROM news_articles WHERE id = :id"),
            {"id": article_id},
        )
        row = result.fetchone()

    if not row:
        logger.warning("Article not found: %s", article_id)
        return {"article_id": article_id, "tickers": [], "status": "not_found"}

    title, full_text = row
    if not full_text:
        return {"article_id": article_id, "tickers": [], "status": "no_text"}

    combined_text = f"{title or ''} {full_text}"

    from pipeline.ml.ner import EntityExtractor

    extractor = EntityExtractor()
    orgs = extractor.extract_organizations(combined_text)

    from pipeline.ml.ticker_resolver import TickerResolver

    resolver = TickerResolver()

    resolved_tickers: list[str] = []

    for org in orgs:
        ticker = resolver.resolve(org)
        if ticker and ticker not in resolved_tickers:
            resolved_tickers.append(ticker)

    ticker_matches = TICKER_PATTERN.findall(combined_text)
    for match in ticker_matches:
        ticker = match[0] or match[1]
        if ticker and ticker not in resolved_tickers:
            resolved_tickers.append(ticker)

    with get_db() as db:
        for ticker in resolved_tickers:
            stock_result = db.execute(
                text("SELECT id FROM stocks WHERE ticker = :ticker"),
                {"ticker": ticker},
            )
            stock_row = stock_result.fetchone()

            if not stock_row:
                continue

            stock_id = stock_row.id

            existing = db.execute(
                text("""
                    SELECT id FROM article_stock_mentions
                    WHERE article_id = :article_id AND stock_id = :stock_id
                """),
                {"article_id": article_id, "stock_id": stock_id},
            ).fetchone()

            if existing:
                continue

            mentioned_as = ticker
            for org in orgs:
                if resolver.resolve(org) == ticker:
                    mentioned_as = org
                    break

            db.execute(
                text("""
                    INSERT INTO article_stock_mentions (
                        article_id, stock_id, relevance_score, mentioned_as, impact_direction
                    ) VALUES (
                        :article_id, :stock_id, :relevance_score, :mentioned_as, :impact_direction
                    )
                """),
                {
                    "article_id": article_id,
                    "stock_id": stock_id,
                    "relevance_score": 0.8,
                    "mentioned_as": mentioned_as,
                    "impact_direction": "neutral",
                },
            )

        db.commit()

    logger.info(
        "Ticker identification complete for article %s: found %d tickers",
        article_id,
        len(resolved_tickers),
    )
    return {"article_id": article_id, "tickers": resolved_tickers, "status": "success"}
