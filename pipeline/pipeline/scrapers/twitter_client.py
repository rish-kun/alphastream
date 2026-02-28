"""Twitter/X client (experimental).

WARNING: Twitter scraping is experimental and may be unreliable due to
API limitations, rate limiting, and frequent changes to the platform.
"""

import logging
import os
from datetime import datetime, timezone

import httpx

from pipeline.config import settings

logger = logging.getLogger(__name__)


class TwitterClient:
    """Experimental Twitter/X scraper for Indian market sentiment.

    This client is experimental and may not work reliably. Twitter/X
    API access is required and subject to rate limits and policy changes.
    """

    def __init__(self) -> None:
        """Initialize the Twitter client."""
        logger.warning(
            "TwitterClient is experimental. Twitter/X API access is required "
            "and may be unreliable due to platform restrictions."
        )
        self._client = None
        self._available = False
        self._bearer_token = settings.TWITTER_BEARER_TOKEN or os.environ.get(
            "TWITTER_BEARER_TOKEN", ""
        )
        if not self._bearer_token:
            logger.warning(
                "Twitter bearer token not configured. Set TWITTER_BEARER_TOKEN "
                "in environment or .env file to enable Twitter scraping."
            )
        else:
            self._available = True
            logger.info("Twitter client initialized with API access")

    def search_tweets(self, query: str, limit: int = 100) -> list[dict]:
        """Search for tweets matching a query.

        Args:
            query: Search query (hashtag, keyword, or cashtag).
            limit: Maximum number of tweets to return.

        Returns:
            List of tweet dicts with text, author, engagement metrics.
        """
        logger.info("Searching tweets: %s (limit=%d)", query, limit)
        if not self._available:
            logger.warning("Twitter scraping unavailable. No bearer token configured.")
            return []

        try:
            headers = {
                "Authorization": f"Bearer {self._bearer_token}",
                "Content-Type": "application/json",
            }
            params = {
                "query": f"{query} lang:en",
                "max_results": min(limit, 100),
                "tweet.fields": "created_at,public_metrics,author_id",
                "expansions": "author_id",
                "user.fields": "username",
            }
            with httpx.Client(timeout=30.0) as client:
                response = client.get(
                    "https://api.twitter.com/2/tweets/search/recent",
                    headers=headers,
                    params=params,
                )
                if response.status_code != 200:
                    logger.error(
                        "Twitter API error: %s - %s",
                        response.status_code,
                        response.text,
                    )
                    return []
                data = response.json()

            tweets = []
            includes = data.get("includes", {})
            users = {u["id"]: u["username"] for u in includes.get("users", [])}

            for tweet in data.get("data", []):
                metrics = tweet.get("public_metrics", {})
                tweets.append(
                    {
                        "id": tweet["id"],
                        "text": tweet["text"],
                        "author": users.get(tweet.get("author_id", ""), "unknown"),
                        "retweet_count": metrics.get("retweet_count", 0),
                        "like_count": metrics.get("like_count", 0),
                        "created_at": tweet.get("created_at", ""),
                    }
                )

            logger.info("Fetched %d tweets for query: %s", len(tweets), query)
            return tweets
        except Exception as e:
            logger.error("Error searching tweets for '%s': %s", query, str(e))
            return []

    def get_user_tweets(self, username: str, limit: int = 50) -> list[dict]:
        """Fetch recent tweets from a specific user.

        Args:
            username: Twitter username (without @ prefix).
            limit: Maximum number of tweets to return.

        Returns:
            List of tweet dicts with text, engagement metrics, timestamp.
        """
        logger.info("Fetching tweets from user: @%s (limit=%d)", username, limit)
        if not self._available:
            logger.warning("Twitter scraping unavailable. No bearer token configured.")
            return []

        try:
            headers = {
                "Authorization": f"Bearer {self._bearer_token}",
                "Content-Type": "application/json",
            }
            params = {
                "max_results": min(limit, 100),
                "tweet.fields": "created_at,public_metrics",
                "expansions": "author_id",
                "user.fields": "username",
            }
            with httpx.Client(timeout=30.0) as client:
                response = client.get(
                    f"https://api.twitter.com/2/users/by/username/{username}/tweets",
                    headers=headers,
                    params=params,
                )
                if response.status_code != 200:
                    logger.error(
                        "Twitter API error: %s - %s",
                        response.status_code,
                        response.text,
                    )
                    return []
                data = response.json()

            tweets = []
            includes = data.get("includes", {})
            users = {u["id"]: u["username"] for u in includes.get("users", [])}

            for tweet in data.get("data", []):
                metrics = tweet.get("public_metrics", {})
                tweets.append(
                    {
                        "id": tweet["id"],
                        "text": tweet["text"],
                        "author": users.get(tweet.get("author_id", ""), username),
                        "retweet_count": metrics.get("retweet_count", 0),
                        "like_count": metrics.get("like_count", 0),
                        "created_at": tweet.get("created_at", ""),
                    }
                )

            logger.info("Fetched %d tweets from user: @%s", len(tweets), username)
            return tweets
        except Exception as e:
            logger.error("Error fetching tweets from @%s: %s", username, str(e))
            return []
