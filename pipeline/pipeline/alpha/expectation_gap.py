"""Expectation Gap metric for sentiment surprise detection.

Measures sentiment surprise vs. rolling baseline.
Positive gap = bullish surprise, negative gap = bearish surprise.
"""

import logging

logger = logging.getLogger(__name__)


def compute_expectation_gap(
    current_sentiment: float, baseline_sentiment: float
) -> float:
    """Compute the Expectation Gap metric.

    Measures how much the current sentiment deviates from the
    rolling baseline. A positive gap indicates a bullish surprise
    (sentiment is more positive than expected), while a negative
    gap indicates a bearish surprise.

    Args:
        current_sentiment: Current sentiment score (-1.0 to 1.0).
        baseline_sentiment: Rolling baseline sentiment (-1.0 to 1.0).

    Returns:
        Expectation gap value (typically -2.0 to 2.0).
    """
    logger.debug(
        "Computing expectation gap: current=%.3f, baseline=%.3f",
        current_sentiment,
        baseline_sentiment,
    )
    # TODO: Implement with rolling window and statistical normalization
    # gap = current_sentiment - baseline_sentiment
    # Optionally normalize by baseline volatility
    return current_sentiment - baseline_sentiment
