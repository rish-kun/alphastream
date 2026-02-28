"""Narrative Velocity metric for news momentum detection.

Measures how quickly a narrative is building in the news cycle.
High velocity with strong sentiment indicates a developing market-moving story.
"""

import logging

logger = logging.getLogger(__name__)


def compute_narrative_velocity(news_share: float, sentiment_magnitude: float) -> float:
    """Compute the Narrative Velocity metric.

    Formula: news_share * 5 * (1 + abs(sentiment))

    A high narrative velocity indicates that a stock/sector is
    dominating the news cycle with strong sentiment, suggesting
    potential price movement.

    Args:
        news_share: Fraction of total news mentioning the entity (0.0 to 1.0).
        sentiment_magnitude: Absolute sentiment score (0.0 to 1.0).

    Returns:
        Narrative velocity score (0.0 to 10.0).
    """
    logger.debug(
        "Computing narrative velocity: news_share=%.3f, sentiment=%.3f",
        news_share,
        sentiment_magnitude,
    )
    # TODO: Implement with time-weighted news volume tracking
    return news_share * 5 * (1 + abs(sentiment_magnitude))
