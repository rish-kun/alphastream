"""Prioritized sentiment analysis tasks for deep research articles."""

import logging
from datetime import datetime
from typing import List

from celery import Task
from sqlalchemy import text

from pipeline.celery_app import app
from pipeline.database import get_db
from pipeline.tasks.sentiment_analysis import analyze_article

logger = logging.getLogger(__name__)

SOURCE_REPUTATION = {
    "Bloomberg": 10,
    "Reuters": 10,
    "CNBC": 9,
    "Economic Times": 9,
    "MoneyControl": 8,
    "LiveMint": 8,
    "Business Standard": 8,
    "Financial Express": 8,
    "The Hindu Business Line": 7,
    "Business Today": 7,
    "Zee Business": 7,
    "NDTV Profit": 7,
    "Mint": 7,
    "The Economic Times": 9,
    "Hindustan Times": 6,
    "Times of India": 5,
    "India Today": 5,
    "News18": 5,
    "Deep Research": 3,
}


def get_source_score(source: str) -> int:
    """Get reputation score for a news source."""
    return SOURCE_REPUTATION.get(source, 5)


@app.task(
    name="pipeline.tasks.prioritized_analysis.analyze_top_articles",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def analyze_top_articles(
    self,
    article_ids: List[str],
    top_n: int = 50,
    priority: str = "recency",
) -> dict:
    """Prioritize and dispatch sentiment analysis for top N articles.

    Args:
        article_ids: List of article IDs to prioritize
        top_n: Number of top articles to analyze (default 50)
        priority: Sorting criteria - "recency" or "relevance"

    Returns:
        dict with status, prioritized count, dispatched count
    """
    if not article_ids:
        return {
            "status": "success",
            "total_articles": 0,
            "prioritized": 0,
            "dispatched": 0,
            "priority_criteria": priority,
        }

    effective_top_n = min(top_n, len(article_ids))

    with get_db() as db:
        placeholders = ",".join([f"'{aid}'" for aid in article_ids])

        if priority == "relevance":
            query = text(f"""
                SELECT id, published_at, source, title
                FROM news_articles
                WHERE id IN ({placeholders})
                ORDER BY 
                    (CASE source
                        WHEN 'Bloomberg' THEN 10
                        WHEN 'Reuters' THEN 10
                        WHEN 'CNBC' THEN 9
                        WHEN 'Economic Times' THEN 9
                        WHEN 'MoneyControl' THEN 8
                        WHEN 'LiveMint' THEN 8
                        WHEN 'Business Standard' THEN 8
                        WHEN 'Financial Express' THEN 8
                        WHEN 'The Hindu Business Line' THEN 7
                        WHEN 'Business Today' THEN 7
                        WHEN 'Zee Business' THEN 7
                        WHEN 'NDTV Profit' THEN 7
                        WHEN 'Mint' THEN 7
                        WHEN 'The Economic Times' THEN 9
                        ELSE 5
                    END) DESC,
                    published_at DESC NULLS LAST
                LIMIT :top_n
            """)
        else:
            query = text(f"""
                SELECT id, published_at, source, title
                FROM news_articles
                WHERE id IN ({placeholders})
                ORDER BY published_at DESC NULLS LAST
                LIMIT :top_n
            """)

        result = db.execute(query, {"top_n": effective_top_n})
        top_articles = result.fetchall()

    dispatched = 0
    for article in top_articles:
        try:
            analyze_article.apply_async(
                args=[str(article.id)],
                countdown=0,
            )
            dispatched += 1
        except Exception as e:
            logger.warning(
                "Failed to dispatch sentiment analysis for article %s: %s",
                article.id,
                e,
            )

    logger.info(
        "Prioritized analysis complete: priority=%s, total=%d, prioritized=%d, dispatched=%d",
        priority,
        len(article_ids),
        effective_top_n,
        dispatched,
    )

    return {
        "status": "success",
        "total_articles": len(article_ids),
        "prioritized": effective_top_n,
        "dispatched": dispatched,
        "priority_criteria": priority,
    }
