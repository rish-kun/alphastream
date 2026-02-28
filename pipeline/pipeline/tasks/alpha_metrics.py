"""Alpha metrics computation task."""

import logging

from pipeline.alpha.composite_signal import compute_composite
from pipeline.alpha.divergence import compute_divergence
from pipeline.alpha.expectation_gap import compute_expectation_gap
from pipeline.alpha.narrative_velocity import compute_narrative_velocity
from pipeline.celery_app import app
from sqlalchemy import text

logger = logging.getLogger(__name__)

TRACKED_SECTORS = [
    "Banking & Finance",
    "Information Technology",
    "Oil & Gas",
    "Pharmaceuticals",
    "Automobiles",
    "FMCG",
    "Metals & Mining",
    "Telecom",
    "Infrastructure",
    "Real Estate",
]


def _clamp(value: float, min_val: float = -9.9999, max_val: float = 9.9999) -> float:
    """Clamp value to a reasonable range."""
    return max(min_val, min(max_val, value))


def _get_news_share(stock_id: str, db) -> float:
    """Calculate news share for a stock (fraction of total articles)."""
    stock_mentions = (
        db.execute(
            text("""
            SELECT COUNT(DISTINCT article_id) as cnt
            FROM article_stock_mentions
            WHERE stock_id = :stock_id
            AND article_id IN (
                SELECT id FROM news_articles
                WHERE scraped_at > now() - interval '24 hours'
            )
        """),
            {"stock_id": stock_id},
        ).scalar()
        or 0
    )

    total_articles = (
        db.execute(
            text("""
            SELECT COUNT(*) FROM news_articles
            WHERE scraped_at > now() - interval '24 hours'
        """)
        ).scalar()
        or 0
    )

    if total_articles == 0:
        return 0.0
    return stock_mentions / total_articles


def _get_price_change(ticker: str) -> float:
    """Get price change percentage from yfinance."""
    try:
        import yfinance as yf

        ticker_data = yf.Ticker(ticker + ".NS")
        hist = ticker_data.history(period="5d")
        if len(hist) >= 2:
            current_price = hist["Close"].iloc[-1]
            previous_price = hist["Close"].iloc[0]
            return (current_price - previous_price) / previous_price
        return 0.0
    except Exception as e:
        logger.warning("Failed to fetch price data for %s: %s", ticker, str(e))
        return 0.0


@app.task(name="pipeline.tasks.alpha_metrics.compute_all")
def compute_all() -> dict:
    """Compute alpha metrics for all tracked stocks and sectors.

    Dispatches individual computation tasks for each stock and sector.
    """
    from pipeline.database import get_db

    logger.info("Starting alpha metrics computation")

    with get_db() as db:
        stocks = db.execute(text("SELECT id, ticker FROM stocks")).fetchall()

    stocks_dispatched = 0
    for stock in stocks:
        compute_stock_alpha.delay(str(stock.id))
        stocks_dispatched += 1

    for sector in TRACKED_SECTORS:
        compute_sector_alpha.delay(sector)

    logger.info(
        "Alpha computation dispatch complete: %d stocks, %d sectors",
        stocks_dispatched,
        len(TRACKED_SECTORS),
    )
    return {
        "stocks_dispatched": stocks_dispatched,
        "sectors_dispatched": len(TRACKED_SECTORS),
    }


@app.task(name="pipeline.tasks.alpha_metrics.compute_stock_alpha")
def compute_stock_alpha(stock_id: str) -> dict:
    """Compute alpha signal metrics for a single stock.

    Calculates:
    - Expectation Gap (sentiment surprise vs baseline)
    - Narrative Velocity (news momentum)
    - Sentiment-Price Divergence
    - Composite Holy Trinity signal

    Args:
        stock_id: Database ID of the stock.

    Returns:
        Dict with stock ID and computed alpha metrics.
    """
    from pipeline.database import get_db

    logger.info("Computing alpha metrics for stock: %s", stock_id)

    with get_db() as db:
        stock_info = db.execute(
            text("SELECT ticker, sector, last_price FROM stocks WHERE id = :id"),
            {"id": stock_id},
        ).fetchone()

        if not stock_info:
            logger.warning("Stock not found: %s", stock_id)
            return {"stock_id": stock_id, "status": "not_found"}

        ticker = stock_info.ticker

        recent_sentiments = db.execute(
            text("""
                SELECT sa.sentiment_score FROM sentiment_analyses sa
                JOIN article_stock_mentions asm ON sa.article_id = asm.article_id
                WHERE asm.stock_id = :stock_id
                AND sa.analyzed_at > now() - interval '24 hours'
            """),
            {"stock_id": stock_id},
        ).fetchall()

        if not recent_sentiments:
            logger.info("No recent sentiment data for stock: %s", stock_id)
            return {"stock_id": stock_id, "status": "no_data"}

        current_sentiment = sum(s.sentiment_score for s in recent_sentiments) / len(
            recent_sentiments
        )

        baseline_result = db.execute(
            text("""
                SELECT AVG(sa.sentiment_score) FROM sentiment_analyses sa
                JOIN article_stock_mentions asm ON sa.article_id = asm.article_id
                WHERE asm.stock_id = :stock_id
                AND sa.analyzed_at > now() - interval '7 days'
            """),
            {"stock_id": stock_id},
        ).scalar()

        baseline_sentiment = (
            float(baseline_result) if baseline_result is not None else 0.0
        )

        expectation_gap = compute_expectation_gap(current_sentiment, baseline_sentiment)
        expectation_gap = _clamp(expectation_gap)

        news_share = _get_news_share(stock_id, db)
        narrative_velocity = compute_narrative_velocity(
            news_share, abs(current_sentiment)
        )
        narrative_velocity = _clamp(narrative_velocity)

        price_change = _get_price_change(ticker)
        divergence = compute_divergence(current_sentiment, price_change)
        divergence = _clamp(divergence)

        composite = compute_composite(expectation_gap, narrative_velocity, divergence)

        db.execute(
            text("""
                INSERT INTO alpha_metrics
                (stock_id, sector, expectation_gap, narrative_velocity, sentiment_divergence,
                 composite_score, signal, conviction, window_hours)
                VALUES (:stock_id, :sector, :expectation_gap, :narrative_velocity,
                        :divergence, :composite_score, :signal, :conviction, 24)
            """),
            {
                "stock_id": stock_id,
                "sector": stock_info.sector,
                "expectation_gap": expectation_gap,
                "narrative_velocity": narrative_velocity,
                "divergence": divergence,
                "composite_score": _clamp(composite["composite_score"]),
                "signal": composite["signal"],
                "conviction": composite["conviction"],
            },
        )

        try:
            from pipeline.utils.publisher import publish_stock_update

            publish_stock_update(
                ticker=ticker,
                alpha_score=composite["composite_score"],
                signal=composite["signal"],
                conviction=composite["conviction"],
            )
        except Exception:
            pass

    logger.info("Alpha computation complete for stock: %s", stock_id)
    return {
        "stock_id": stock_id,
        "ticker": ticker,
        "expectation_gap": expectation_gap,
        "narrative_velocity": narrative_velocity,
        "divergence": divergence,
        "composite_score": composite["composite_score"],
        "signal": composite["signal"],
        "conviction": composite["conviction"],
        "status": "success",
    }


@app.task(name="pipeline.tasks.alpha_metrics.compute_sector_alpha")
def compute_sector_alpha(sector: str) -> dict:
    """Compute aggregate alpha signal for an entire sector.

    Aggregates individual stock signals within the sector and
    computes sector-level sentiment trends.

    Args:
        sector: Name of the market sector.

    Returns:
        Dict with sector name and aggregated alpha metrics.
    """
    from pipeline.database import get_db

    logger.info("Computing alpha metrics for sector: %s", sector)

    with get_db() as db:
        stocks_in_sector = db.execute(
            text("SELECT id, ticker FROM stocks WHERE sector = :sector"),
            {"sector": sector},
        ).fetchall()

        if not stocks_in_sector:
            logger.warning("No stocks found in sector: %s", sector)
            return {"sector": sector, "status": "no_stocks"}

        stock_ids = [str(s.id) for s in stocks_in_sector]
        if not stock_ids:
            return {"sector": sector, "status": "no_stocks"}

        recent_sentiments = db.execute(
            text("""
                SELECT sa.sentiment_score FROM sentiment_analyses sa
                JOIN article_stock_mentions asm ON sa.article_id = asm.article_id
                WHERE asm.stock_id IN :stock_ids
                AND sa.analyzed_at > now() - interval '24 hours'
            """),
            {"stock_ids": tuple(stock_ids)},
        ).fetchall()

        if not recent_sentiments:
            logger.info("No recent sentiment data for sector: %s", sector)
            return {"sector": sector, "status": "no_data"}

        current_sentiment = sum(s.sentiment_score for s in recent_sentiments) / len(
            recent_sentiments
        )

        baseline_result = db.execute(
            text("""
                SELECT AVG(sa.sentiment_score) FROM sentiment_analyses sa
                JOIN article_stock_mentions asm ON sa.article_id = asm.article_id
                WHERE asm.stock_id IN :stock_ids
                AND sa.analyzed_at > now() - interval '7 days'
            """),
            {"stock_ids": tuple(stock_ids)},
        ).scalar()

        baseline_sentiment = (
            float(baseline_result) if baseline_result is not None else 0.0
        )

        expectation_gap = compute_expectation_gap(current_sentiment, baseline_sentiment)
        expectation_gap = _clamp(expectation_gap)

        total_mentions = (
            db.execute(
                text("""
                SELECT COUNT(DISTINCT asm.article_id) FROM article_stock_mentions asm
                JOIN news_articles na ON asm.article_id = na.id
                WHERE asm.stock_id IN :stock_ids
                AND na.scraped_at > now() - interval '24 hours'
            """),
                {"stock_ids": tuple(stock_ids)},
            ).scalar()
            or 0
        )

        total_articles = (
            db.execute(
                text(
                    "SELECT COUNT(*) FROM news_articles WHERE scraped_at > now() - interval '24 hours'"
                )
            ).scalar()
            or 0
        )

        news_share = total_mentions / total_articles if total_articles > 0 else 0.0
        narrative_velocity = compute_narrative_velocity(
            news_share, abs(current_sentiment)
        )
        narrative_velocity = _clamp(narrative_velocity)

        price_changes = []
        for stock in stocks_in_sector[:10]:
            pc = _get_price_change(stock.ticker)
            if pc != 0.0:
                price_changes.append(pc)

        avg_price_change = (
            sum(price_changes) / len(price_changes) if price_changes else 0.0
        )
        divergence = compute_divergence(current_sentiment, avg_price_change)
        divergence = _clamp(divergence)

        composite = compute_composite(expectation_gap, narrative_velocity, divergence)

        db.execute(
            text("""
                INSERT INTO alpha_metrics
                (stock_id, sector, expectation_gap, narrative_velocity, sentiment_divergence,
                 composite_score, signal, conviction, window_hours)
                VALUES (NULL, :sector, :expectation_gap, :narrative_velocity,
                        :divergence, :composite_score, :signal, :conviction, 24)
            """),
            {
                "sector": sector,
                "expectation_gap": expectation_gap,
                "narrative_velocity": narrative_velocity,
                "divergence": divergence,
                "composite_score": _clamp(composite["composite_score"]),
                "signal": composite["signal"],
                "conviction": composite["conviction"],
            },
        )

    logger.info("Sector alpha computation complete: %s", sector)
    return {
        "sector": sector,
        "stocks_count": len(stocks_in_sector),
        "expectation_gap": expectation_gap,
        "narrative_velocity": narrative_velocity,
        "divergence": divergence,
        "composite_score": composite["composite_score"],
        "signal": composite["signal"],
        "conviction": composite["conviction"],
        "status": "success",
    }
