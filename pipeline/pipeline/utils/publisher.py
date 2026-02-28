"""Redis publisher for cross-process WebSocket messaging."""

import json
import logging

import redis

from pipeline.config import settings

logger = logging.getLogger(__name__)

_redis_client: redis.Redis | None = None


def _get_redis() -> redis.Redis:
    """Get or create Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client


def publish_event(channel: str, data: dict) -> bool:
    """Publish an event to Redis pub/sub.

    Args:
        channel: The channel to publish to (e.g., "feed", "stock:RELIANCE", "sentiment")
        data: The data to publish (will be JSON serialized)

    Returns:
        True if published successfully, False otherwise
    """
    try:
        client = _get_redis()
        client.publish(channel, json.dumps(data))
        logger.debug("Published event to channel: %s", channel)
        return True
    except Exception as e:
        logger.error("Failed to publish to channel %s: %s", channel, e)
        return False


def publish_new_article(
    article_id: str, title: str, source: str, url: str, published_at: str | None = None
) -> bool:
    """Publish a new article event to the feed channel."""
    return publish_event(
        "feed",
        {
            "type": "new_article",
            "data": {
                "id": article_id,
                "title": title,
                "source": source,
                "url": url,
                "published_at": published_at,
            },
        },
    )


def publish_sentiment_update(
    article_id: str,
    sentiment_score: float,
    confidence: float,
    explanation: str | None = None,
) -> bool:
    """Publish a sentiment analysis update event."""
    return publish_event(
        "sentiment",
        {
            "type": "sentiment_update",
            "data": {
                "article_id": article_id,
                "sentiment_score": sentiment_score,
                "confidence": confidence,
                "explanation": explanation,
            },
        },
    )


def publish_stock_update(
    ticker: str,
    alpha_score: float | None = None,
    signal: str | None = None,
    conviction: str | None = None,
) -> bool:
    """Publish a stock alpha update event."""
    return publish_event(
        f"stock:{ticker}",
        {
            "type": "stock_update",
            "data": {
                "ticker": ticker,
                "alpha_score": alpha_score,
                "signal": signal,
                "conviction": conviction,
            },
        },
    )
