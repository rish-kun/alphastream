"""Sentiment analysis task using FinBERT + selective LLM ensemble."""

import json
import logging
from typing import Any

from celery import Task
from sqlalchemy import text

from pipeline.celery_app import app
from pipeline.config import settings
from pipeline.database import check_schema_ready, get_db

logger = logging.getLogger(__name__)

_FINBERT_ANALYZER = None


def _get_finbert_analyzer():
    global _FINBERT_ANALYZER
    if _FINBERT_ANALYZER is None:
        from pipeline.ml.finbert import FinBERTAnalyzer

        _FINBERT_ANALYZER = FinBERTAnalyzer()
    return _FINBERT_ANALYZER


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _has_llm_keys() -> bool:
    return bool(settings.GEMINI_API_KEYS or settings.OPENROUTER_API_KEYS)


def _should_use_llm(finbert_score: float, finbert_confidence: float) -> bool:
    if not settings.SENTIMENT_ENABLE_LLM:
        return False
    if not _has_llm_keys():
        return False
    if finbert_confidence < settings.SENTIMENT_LLM_TRIGGER_CONFIDENCE:
        return True
    return abs(finbert_score) <= settings.SENTIMENT_LLM_TRIGGER_NEUTRAL_BAND


def _build_analysis_text(title: str, full_text: str) -> str:
    cleaned_body = " ".join((full_text or "").split())
    cleaned_title = " ".join((title or "").split())
    if not cleaned_title:
        return cleaned_body
    return f"Headline: {cleaned_title}\n\nArticle: {cleaned_body}"


def _run_llm_analysis(text_body: str, source: str) -> tuple[dict | None, str | None]:
    if not _has_llm_keys():
        return None, None

    provider_order = settings.SENTIMENT_LLM_PROVIDER_ORDER or ["gemini", "openrouter"]
    context = f"source: {source}"

    for provider in provider_order:
        provider = provider.lower().strip()
        if provider == "gemini" and settings.GEMINI_API_KEYS:
            try:
                from pipeline.llm.gemini_client import GeminiClient

                client = GeminiClient(settings.GEMINI_API_KEYS)
                result = client.analyze_sentiment(text_body, context=context)
                return result, "gemini"
            except Exception:
                logger.warning("Gemini analysis failed", exc_info=True)
                continue
        if provider == "openrouter" and settings.OPENROUTER_API_KEYS:
            try:
                from pipeline.llm.openrouter_client import OpenRouterClient

                client = OpenRouterClient(settings.OPENROUTER_API_KEYS)
                result = client.analyze_sentiment(text_body, context=context)
                return result, "openrouter"
            except Exception:
                logger.warning("OpenRouter analysis failed", exc_info=True)
                continue

    return None, None


def _combine_scores(
    finbert_score: float,
    finbert_confidence: float,
    llm_score: float | None,
    llm_confidence: float | None,
) -> tuple[float, float]:
    if llm_score is None:
        return (
            _clamp(finbert_score, -1.0, 1.0),
            _clamp(finbert_confidence, 0.0, 1.0),
        )

    llm_conf = _clamp(llm_confidence or 0.0, 0.0, 1.0)
    fin_conf = _clamp(finbert_confidence, 0.0, 1.0)

    local_weight = settings.SENTIMENT_LOCAL_WEIGHT * max(fin_conf, 0.10)
    llm_weight = settings.SENTIMENT_LLM_WEIGHT * max(llm_conf, 0.10)
    total = local_weight + llm_weight

    if total <= 0:
        return 0.0, 0.0

    score = ((finbert_score * local_weight) + (llm_score * llm_weight)) / total
    confidence = (
        (fin_conf * settings.SENTIMENT_LOCAL_WEIGHT)
        + (llm_conf * settings.SENTIMENT_LLM_WEIGHT)
    ) / max(settings.SENTIMENT_LOCAL_WEIGHT + settings.SENTIMENT_LLM_WEIGHT, 1e-6)

    return _clamp(score, -1.0, 1.0), _clamp(confidence, 0.0, 1.0)


@app.task(name="pipeline.tasks.sentiment_analysis.analyze_pending")
def analyze_pending() -> dict:
    """Dispatch sentiment analysis for news articles missing sentiment rows."""
    if not check_schema_ready():
        return {"status": "skipped", "reason": "database schema not ready"}

    logger.info("Starting sentiment analysis for pending articles")

    with get_db() as db:
        result = db.execute(
            text("""
                SELECT id FROM news_articles
                WHERE full_text IS NOT NULL
                AND id NOT IN (SELECT article_id FROM sentiment_analyses)
                ORDER BY published_at DESC
                LIMIT :limit
            """),
            {"limit": settings.SENTIMENT_PENDING_BATCH_SIZE},
        )
        rows = result.fetchall()

    count = 0
    for row in rows:
        analyze_article.delay(str(row.id))
        count += 1

    logger.info("Sentiment analysis dispatch complete: %d articles dispatched", count)
    return {"articles_dispatched": count}


@app.task(
    name="pipeline.tasks.sentiment_analysis.analyze_article",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
)
def analyze_article(self: Task, article_id: str, force_reanalyze: bool = False) -> dict:
    """Run sentiment analysis on one article with optional forced re-analysis."""
    logger.info(
        "Analyzing sentiment for article=%s (force_reanalyze=%s)",
        article_id,
        force_reanalyze,
    )

    with get_db() as db:
        row = db.execute(
            text("""
                SELECT
                    n.title,
                    n.full_text,
                    n.source,
                    EXISTS(
                        SELECT 1 FROM sentiment_analyses s WHERE s.article_id = n.id
                    ) AS already_analyzed
                FROM news_articles n
                WHERE n.id = :id
            """),
            {"id": article_id},
        ).fetchone()

    if not row:
        logger.warning("Article not found: %s", article_id)
        return {"article_id": article_id, "status": "not_found"}

    if len(row) >= 4:
        title, full_text, source, already_analyzed = row
    else:
        title, full_text, source = row
        already_analyzed = False

    if already_analyzed and not force_reanalyze:
        return {"article_id": article_id, "status": "already_analyzed"}

    if not full_text:
        logger.info("Article has no full_text: %s", article_id)
        return {"article_id": article_id, "status": "no_text"}

    analysis_text = _build_analysis_text(title, full_text)
    analyzer = _get_finbert_analyzer()
    finbert_result = analyzer.analyze(analysis_text)
    finbert_score = _clamp(_to_float(finbert_result.get("score")), -1.0, 1.0)
    finbert_confidence = _clamp(
        _to_float(finbert_result.get("confidence")),
        0.0,
        1.0,
    )

    llm_result = None
    llm_provider = None
    llm_score = None
    llm_confidence = None

    if _should_use_llm(finbert_score, finbert_confidence):
        llm_input = analysis_text[: settings.SENTIMENT_LLM_MAX_CHARS]
        llm_result, llm_provider = _run_llm_analysis(llm_input, source=source)
        if llm_result:
            llm_score = _clamp(_to_float(llm_result.get("sentiment_score")), -1.0, 1.0)
            llm_confidence = _clamp(
                _to_float(llm_result.get("confidence")),
                0.0,
                1.0,
            )

    ensemble_score, confidence = _combine_scores(
        finbert_score=finbert_score,
        finbert_confidence=finbert_confidence,
        llm_score=llm_score,
        llm_confidence=llm_confidence,
    )

    if llm_result:
        explanation = llm_result.get("explanation") or "LLM-augmented sentiment analysis"
        impact_timeline = llm_result.get("impact_timeline") or "unknown"
    else:
        label = finbert_result.get("label", "neutral")
        explanation = (
            f"FinBERT-only analysis ({label}) with confidence "
            f"{round(finbert_confidence * 100)}%."
        )
        impact_timeline = "unknown"

    raw_payload = {
        "finbert": finbert_result,
        "llm": llm_result,
        "metadata": {
            "llm_used": bool(llm_result),
            "llm_provider": llm_provider,
            "force_reanalyze": force_reanalyze,
        },
    }

    try:
        with get_db() as db:
            # Keep one canonical sentiment row per article.
            db.execute(
                text("DELETE FROM sentiment_analyses WHERE article_id = :article_id"),
                {"article_id": article_id},
            )
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
                    "sentiment_score": ensemble_score,
                    "confidence": confidence,
                    "explanation": explanation,
                    "impact_timeline": impact_timeline,
                    "finbert_score": finbert_score,
                    "llm_score": llm_score,
                    "llm_provider": llm_provider,
                    "raw_response": json.dumps(raw_payload),
                },
            )
            db.commit()

        try:
            from pipeline.utils.publisher import publish_sentiment_update

            publish_sentiment_update(
                article_id=article_id,
                sentiment_score=ensemble_score,
                confidence=confidence,
                explanation=explanation,
            )
        except Exception:
            logger.debug("Failed to publish sentiment update for %s", article_id)

        return {
            "article_id": article_id,
            "status": "success",
            "finbert_score": finbert_score,
            "llm_score": llm_score,
            "ensemble_score": ensemble_score,
            "confidence": confidence,
            "llm_provider": llm_provider,
        }
    except Exception as exc:
        logger.error("Failed to save sentiment analysis for %s: %s", article_id, exc)
        raise self.retry(exc=exc)
