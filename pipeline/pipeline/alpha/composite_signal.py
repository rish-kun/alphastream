"""Composite signal combiner (Holy Trinity).

Combines Expectation Gap, Narrative Velocity, and Sentiment-Price Divergence
into a single actionable trading signal with conviction scoring.
"""

import logging

logger = logging.getLogger(__name__)

# Signal thresholds
STRONG_BUY_THRESHOLD = 0.5
BUY_THRESHOLD = 0.2
SELL_THRESHOLD = -0.2
STRONG_SELL_THRESHOLD = -0.5


def compute_composite(
    expectation_gap: float,
    narrative_velocity: float,
    divergence: float,
) -> dict:
    """Compute the Holy Trinity composite signal.

    Combines three alpha metrics with weighted averaging:
    - Expectation Gap: 45% weight (strongest predictor)
    - Narrative Velocity: 30% weight (momentum indicator)
    - Divergence: 25% weight (contrarian indicator)

    Args:
        expectation_gap: Expectation Gap metric value.
        narrative_velocity: Narrative Velocity metric value.
        divergence: Sentiment-Price Divergence metric value.

    Returns:
        Dict with:
            - composite_score: Weighted composite value (-1.0 to 1.0)
            - signal: One of strong_buy, buy, hold, sell, strong_sell
            - conviction: Confidence in the signal (0.0 to 1.0)
    """
    # Weighted combination
    composite_score = (
        0.45 * expectation_gap + 0.30 * narrative_velocity + 0.25 * divergence
    )

    # Map to signal
    if composite_score > STRONG_BUY_THRESHOLD:
        signal = "strong_buy"
    elif composite_score > BUY_THRESHOLD:
        signal = "buy"
    elif composite_score > SELL_THRESHOLD:
        signal = "hold"
    elif composite_score > STRONG_SELL_THRESHOLD:
        signal = "sell"
    else:
        signal = "strong_sell"

    # Conviction is based on the absolute magnitude of the composite score
    # Normalized to 0-1 range (scores beyond +/-1 are clamped)
    conviction = min(abs(composite_score), 1.0)

    logger.info(
        "Composite signal: score=%.3f, signal=%s, conviction=%.3f "
        "(eg=%.3f, nv=%.3f, div=%.3f)",
        composite_score,
        signal,
        conviction,
        expectation_gap,
        narrative_velocity,
        divergence,
    )

    return {
        "composite_score": composite_score,
        "signal": signal,
        "conviction": conviction,
    }
