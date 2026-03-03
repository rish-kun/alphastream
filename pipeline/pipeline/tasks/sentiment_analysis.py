"""Sentiment analysis task using FinBERT + selective LLM ensemble."""

import json
import logging
from math import ceil
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


def _run_all_llm_analyses(
    text_body: str,
    source: str,
) -> tuple[dict[str, dict], dict[str, str]]:
    """Run all configured LLM providers and collect successful responses."""
    if not _has_llm_keys():
        return {}, {}

    results: dict[str, dict] = {}
    failures: dict[str, str] = {}
    provider_order = settings.SENTIMENT_LLM_PROVIDER_ORDER or [
        "gemini", "openrouter"]
    context = f"source: {source}"

    def _attempt_with_fallback_models(provider_name: str) -> tuple[dict | None, str | None]:
        retries = max(0, settings.SENTIMENT_LLM_FALLBACK_RETRIES)

        if provider_name == "gemini":
            if not settings.GEMINI_API_KEYS:
                return None, "missing_api_keys"
            from pipeline.llm.gemini_client import GeminiClient

            client_cls = GeminiClient
            api_keys = settings.GEMINI_API_KEYS
            primary_model = settings.SENTIMENT_GEMINI_MODEL
            fallback_model = settings.SENTIMENT_GEMINI_FALLBACK_MODEL
        elif provider_name == "openrouter":
            if not settings.OPENROUTER_API_KEYS:
                return None, "missing_api_keys"
            from pipeline.llm.openrouter_client import OpenRouterClient

            client_cls = OpenRouterClient
            api_keys = settings.OPENROUTER_API_KEYS
            primary_model = settings.SENTIMENT_OPENROUTER_MODEL
            fallback_model = settings.SENTIMENT_OPENROUTER_FALLBACK_MODEL
        else:
            return None, "unsupported_provider"

        attempts = [primary_model] + [fallback_model] * retries
        attempt_errors: list[str] = []

        for attempt_idx, model_name in enumerate(attempts, start=1):
            try:
                client = client_cls(api_keys=api_keys, model_name=model_name)
                result = client.analyze_sentiment(
                    text_body,
                    context=context,
                    fail_silently=False,
                )
                return result, None
            except Exception as exc:
                failure_msg = f"attempt={attempt_idx};model={model_name};error={exc}"
                attempt_errors.append(failure_msg)
                logger.warning(
                    "%s sentiment attempt failed (%d/%d): %s",
                    provider_name,
                    attempt_idx,
                    len(attempts),
                    exc,
                    exc_info=True,
                )

        return None, " | ".join(attempt_errors) if attempt_errors else "unknown_error"

    for provider in provider_order:
        provider = provider.lower().strip()
        result, failure = _attempt_with_fallback_models(provider)
        if result is not None:
            results[provider] = result
        else:
            failures[provider] = failure or "unknown_error"

    return results, failures


def _combine_weighted_scores(scores: dict[str, float], confidences: dict[str, float]) -> tuple[float, float]:
    """Combine scores from available models with normalized configured weights."""
    configured_weights = {
        "local": settings.SENTIMENT_LOCAL_WEIGHT,
        "gemini": settings.SENTIMENT_GEMINI_WEIGHT,
        "openrouter": settings.SENTIMENT_OPENROUTER_WEIGHT,
    }

    available = [model for model in scores if model in configured_weights]
    if not available:
        return 0.0, 0.0

    base_weight_sum = sum(configured_weights[model] for model in available)
    if base_weight_sum <= 0:
        return 0.0, 0.0

    weighted_sum = 0.0
    confidence_sum = 0.0
    for model in available:
        normalized_weight = configured_weights[model] / base_weight_sum
        model_confidence = _clamp(confidences.get(model, 0.0), 0.0, 1.0)
        weighted_sum += _clamp(scores[model], -1.0, 1.0) * normalized_weight
        confidence_sum += model_confidence * normalized_weight

    return _clamp(weighted_sum, -1.0, 1.0), _clamp(confidence_sum, 0.0, 1.0)


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

    logger.info(
        "Sentiment analysis dispatch complete: %d articles dispatched", count)
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

    llm_results: dict[str, dict] = {}
    llm_failures: dict[str, str] = {}
    gemini_score = None
    openrouter_score = None
    gemini_confidence = None
    openrouter_confidence = None

    should_run_llm = (
        settings.SENTIMENT_ENABLE_LLM
        and _has_llm_keys()
        and (
            force_reanalyze
            or settings.SENTIMENT_ALWAYS_USE_LLM
            or _should_use_llm(finbert_score, finbert_confidence)
        )
    )

    if should_run_llm:
        llm_input = analysis_text[: settings.SENTIMENT_LLM_MAX_CHARS]
        llm_results, llm_failures = _run_all_llm_analyses(
            llm_input, source=source)
        if "gemini" in llm_results:
            gemini_score = _clamp(
                _to_float(llm_results["gemini"].get("sentiment_score")),
                -1.0,
                1.0,
            )
            gemini_confidence = _clamp(
                _to_float(llm_results["gemini"].get("confidence")),
                0.0,
                1.0,
            )
        if "openrouter" in llm_results:
            openrouter_score = _clamp(
                _to_float(llm_results["openrouter"].get("sentiment_score")),
                -1.0,
                1.0,
            )
            openrouter_confidence = _clamp(
                _to_float(llm_results["openrouter"].get("confidence")),
                0.0,
                1.0,
            )

    scores = {"local": finbert_score}
    confidences = {"local": finbert_confidence}
    if gemini_score is not None:
        scores["gemini"] = gemini_score
        confidences["gemini"] = gemini_confidence or 0.0
    if openrouter_score is not None:
        scores["openrouter"] = openrouter_score
        confidences["openrouter"] = openrouter_confidence or 0.0

    ensemble_score, confidence = _combine_weighted_scores(
        scores=scores, confidences=confidences)

    blended_llm_score = None
    llm_provider = None
    llm_confidence = None
    if gemini_score is not None and openrouter_score is not None:
        blended_llm_score, llm_confidence = _combine_weighted_scores(
            scores={"gemini": gemini_score, "openrouter": openrouter_score},
            confidences={
                "gemini": gemini_confidence or 0.0,
                "openrouter": openrouter_confidence or 0.0,
            },
        )
        llm_provider = "ensemble"
    elif gemini_score is not None:
        blended_llm_score = gemini_score
        llm_provider = "gemini"
        llm_confidence = gemini_confidence
    elif openrouter_score is not None:
        blended_llm_score = openrouter_score
        llm_provider = "openrouter"
        llm_confidence = openrouter_confidence

    if llm_results:
        # Favor Gemini explanation when available, then OpenRouter.
        explanation = (
            llm_results.get("gemini", {}).get("explanation")
            or llm_results.get("openrouter", {}).get("explanation")
            or "Multi-model sentiment analysis"
        )
        impact_timeline = (
            llm_results.get("gemini", {}).get("impact_timeline")
            or llm_results.get("openrouter", {}).get("impact_timeline")
            or "unknown"
        )
    else:
        label = finbert_result.get("label", "neutral")
        explanation = (
            f"FinBERT-only analysis ({label}) with confidence "
            f"{round(finbert_confidence * 100)}%."
        )
        impact_timeline = "unknown"

    raw_payload = {
        "finbert": finbert_result,
        "llm": llm_results,
        "weights": {
            "local": settings.SENTIMENT_LOCAL_WEIGHT,
            "gemini": settings.SENTIMENT_GEMINI_WEIGHT,
            "openrouter": settings.SENTIMENT_OPENROUTER_WEIGHT,
        },
        "metadata": {
            "llm_used": bool(llm_results),
            "llm_provider": llm_provider,
            "llm_failures": llm_failures,
            "llm_confidence": llm_confidence,
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
                    "llm_score": blended_llm_score,
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
            logger.debug(
                "Failed to publish sentiment update for %s", article_id)

        return {
            "article_id": article_id,
            "status": "success",
            "finbert_score": finbert_score,
            "llm_score": blended_llm_score,
            "ensemble_score": ensemble_score,
            "confidence": confidence,
            "llm_provider": llm_provider,
        }
    except Exception as exc:
        logger.error(
            "Failed to save sentiment analysis for %s: %s", article_id, exc)
        raise self.retry(exc=exc)


@app.task(name="pipeline.tasks.sentiment_analysis.reanalyze_all", bind=True)
def reanalyze_all(
    self: Task,
    force_reanalyze: bool = True,
    batch_size: int | None = None,
    batch_delay_seconds: int | None = None,
    max_articles: int | None = None,
) -> dict:
    """Queue re-analysis for all articles in throttled batches."""
    if not check_schema_ready():
        return {"status": "skipped", "reason": "database schema not ready"}

    effective_batch_size = max(
        1, batch_size or settings.SENTIMENT_REANALYZE_ALL_BATCH_SIZE)
    effective_batch_delay = max(
        0,
        batch_delay_seconds or settings.SENTIMENT_REANALYZE_ALL_BATCH_DELAY_SECONDS,
    )
    effective_max_articles = max_articles or settings.SENTIMENT_REANALYZE_ALL_MAX_ARTICLES

    with get_db() as db:
        total_result = db.execute(
            text("SELECT COUNT(*) FROM news_articles"),
        )
        total_articles = int(total_result.scalar_one() or 0)

        rows = db.execute(
            text(
                """
                SELECT id
                FROM news_articles
                ORDER BY published_at DESC NULLS LAST
                LIMIT :max_articles
                """
            ),
            {"max_articles": effective_max_articles},
        ).fetchall()

    to_dispatch = len(rows)
    if to_dispatch == 0:
        return {
            "status": "success",
            "total_articles": total_articles,
            "targeted_articles": 0,
            "dispatched": 0,
            "batch_size": effective_batch_size,
            "batch_delay_seconds": effective_batch_delay,
        }

    dispatched = 0
    for index, row in enumerate(rows):
        countdown = (index // effective_batch_size) * effective_batch_delay
        analyze_article.apply_async(
            args=[str(row.id)],
            kwargs={"force_reanalyze": force_reanalyze},
            countdown=countdown,
        )
        dispatched += 1

        if dispatched % effective_batch_size == 0 or dispatched == to_dispatch:
            self.update_state(
                state="PROGRESS",
                meta={
                    "total_articles": total_articles,
                    "targeted_articles": to_dispatch,
                    "dispatched": dispatched,
                    "batch_size": effective_batch_size,
                    "batch_delay_seconds": effective_batch_delay,
                    "queued_batches": ceil(dispatched / effective_batch_size),
                },
            )

    return {
        "status": "success",
        "total_articles": total_articles,
        "targeted_articles": to_dispatch,
        "dispatched": dispatched,
        "batch_size": effective_batch_size,
        "batch_delay_seconds": effective_batch_delay,
        "queued_batches": ceil(to_dispatch / effective_batch_size),
    }
