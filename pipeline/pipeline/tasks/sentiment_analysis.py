"""Sentiment analysis task using FinBERT and LLM ensemble."""

import json
import logging

from celery import Task
from sqlalchemy import text

from pipeline.celery_app import app
from pipeline.config import settings
from pipeline.database import get_db

logger = logging.getLogger(__name__)


@app.task(name="pipeline.tasks.sentiment_analysis.analyze_pending")
def analyze_pending() -> dict:
    """Run sentiment analysis on all articles pending analysis.

    Queries the database for articles with full text but no sentiment
    score, and dispatches individual analysis tasks.
    """
    logger.info("Starting sentiment analysis for pending articles")

    with get_db() as db:
        result = db.execute(
            text("""
                SELECT id FROM news_articles
                WHERE full_text IS NOT NULL
                AND id NOT IN (SELECT article_id FROM sentiment_analyses)
                LIMIT 50
            """),
        )
        rows = result.fetchall()

    count = 0
    for row in rows:
        article_id = str(row.id)
        analyze_article.delay(article_id)
        count += 1

    logger.info("Sentiment analysis dispatch complete: %d articles dispatched", count)
    return {"articles_dispatched": count}


@app.task(
    name="pipeline.tasks.sentiment_analysis.analyze_article",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
)
def analyze_article(self: Task, article_id: str) -> dict:
    """Run sentiment analysis on a single article.

    Uses an ensemble approach:
    1. FinBERT for base financial sentiment
    2. Gemini/OpenRouter LLM for nuanced analysis
    3. Weighted combination of both scores

    Args:
        article_id: Database ID of the article to analyze.

    Returns:
        Dict with article ID and sentiment analysis results.
    """
    logger.info("Analyzing sentiment for article: %s", article_id)

    with get_db() as db:
        result = db.execute(
            text("SELECT title, full_text, source FROM news_articles WHERE id = :id"),
            {"id": article_id},
        )
        row = result.fetchone()

    if not row:
        logger.warning("Article not found: %s", article_id)
        return {"article_id": article_id, "status": "not_found"}

    title, full_text, source = row

    if not full_text:
        logger.info("Article has no full_text: %s", article_id)
        return {"article_id": article_id, "status": "no_text"}

    from pipeline.ml.finbert import FinBERTAnalyzer

    analyzer = FinBERTAnalyzer()
    finbert_result = analyzer.analyze(full_text)

    finbert_score = finbert_result["score"]
    finbert_confidence = finbert_result["confidence"]

    llm_result = None
    llm_score = None
    llm_provider = None

    try:
        if settings.GEMINI_API_KEYS:
            from pipeline.llm.gemini_client import GeminiClient

            client = GeminiClient(settings.GEMINI_API_KEYS)
            llm_result = client.analyze_sentiment(
                full_text, context=f"source: {source}"
            )
            llm_score = llm_result.get("sentiment_score", 0.0)
            llm_provider = "gemini"
    except Exception as e:
        logger.warning("Gemini analysis failed: %s", e)

    if llm_result is None and settings.OPENROUTER_API_KEYS:
        try:
            from pipeline.llm.openrouter_client import OpenRouterClient

            client = OpenRouterClient(settings.OPENROUTER_API_KEYS)
            llm_result = client.analyze_sentiment(
                full_text, context=f"source: {source}"
            )
            llm_score = llm_result.get("sentiment_score", 0.0)
            llm_provider = "openrouter"
        except Exception as e:
            logger.warning("OpenRouter analysis failed: %s", e)

    if llm_score is not None and finbert_score is not None:
        ensemble = 0.4 * finbert_score + 0.6 * llm_score
        confidence = (finbert_confidence + llm_result.get("confidence", 0.0)) / 2
    elif finbert_score is not None:
        ensemble = finbert_score
        confidence = finbert_confidence
    elif llm_score is not None:
        ensemble = llm_score
        confidence = llm_result.get("confidence", 0.0)
    else:
        ensemble = 0.0
        confidence = 0.0

    explanation = "FinBERT analysis"
    impact_timeline = "unknown"
    raw_response = None

    if llm_result:
        explanation = llm_result.get("explanation", "FinBERT analysis")
        impact_timeline = llm_result.get("impact_timeline", "unknown")
        raw_response = json.dumps(llm_result)

    try:
        with get_db() as db:
            db.execute(
                text("""
                    INSERT INTO sentiment_analyses (
                        article_id, sentiment_score, confidence, explanation,
                        impact_timeline, finbert_score, llm_score, llm_provider, raw_response
                    ) VALUES (
                        :article_id, :sentiment_score, :confidence, :explanation,
                        :impact_timeline, :finbert_score, :llm_score, :llm_provider,
                        CAST(:raw_response AS jsonb)
                    )
                """),
                {
                    "article_id": article_id,
                    "sentiment_score": ensemble,
                    "confidence": confidence,
                    "explanation": explanation,
                    "impact_timeline": impact_timeline,
                    "finbert_score": finbert_score,
                    "llm_score": llm_score,
                    "llm_provider": llm_provider,
                    "raw_response": json.dumps(raw_response) if raw_response else None,
                },
            )
            db.commit()

        try:
            from pipeline.utils.publisher import publish_sentiment_update

            publish_sentiment_update(
                article_id=article_id,
                sentiment_score=ensemble,
                confidence=confidence,
                explanation=explanation,
            )
        except Exception:
            pass

        logger.info("Sentiment analysis complete for article: %s", article_id)
        return {
            "article_id": article_id,
            "finbert_score": finbert_score,
            "llm_score": llm_score,
            "ensemble_score": ensemble,
            "confidence": confidence,
            "status": "success",
        }

    except Exception as exc:
        logger.error("Failed to save sentiment analysis: %s", exc)
        raise self.retry(exc=exc)
