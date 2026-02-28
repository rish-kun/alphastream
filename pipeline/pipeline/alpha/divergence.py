"""Sentiment-Price Divergence metric.

Detects divergence between news sentiment and price action.
Strong sentiment with low news share signals potential smart money activity.
"""

import logging

logger = logging.getLogger(__name__)


def compute_divergence(sentiment: float, price_change: float) -> float:
    """Compute the Sentiment-Price Divergence metric.

    Measures the gap between news sentiment direction and actual
    price movement. A positive divergence (bullish sentiment, falling price)
    may indicate an upcoming reversal. Strong sentiment with minimal
    price impact signals potential smart money positioning.

    Args:
        sentiment: Current sentiment score (-1.0 to 1.0).
        price_change: Percentage price change (e.g., 0.05 for +5%).

    Returns:
        Divergence score (-2.0 to 2.0).
    """
    logger.debug(
        "Computing divergence: sentiment=%.3f, price_change=%.3f",
        sentiment,
        price_change,
    )
    # TODO: Implement with time-lagged correlation analysis
    # Divergence = sentiment - normalized_price_change
    # Positive divergence: sentiment is more bullish than price suggests
    # Negative divergence: sentiment is more bearish than price suggests
    return sentiment - price_change
