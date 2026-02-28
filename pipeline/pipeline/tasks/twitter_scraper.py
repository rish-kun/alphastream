"""Twitter/X scraping task (experimental)."""

import logging

from celery import Task
from sqlalchemy import text

from pipeline.celery_app import app
from pipeline.database import check_schema_ready, get_db
from pipeline.scrapers.twitter_client import TwitterClient

logger = logging.getLogger(__name__)

DEFAULT_QUERIES = [
    "#Nifty50",
    "#Sensex",
    "#IndianStockMarket",
    "#NSE",
    "#BSE",
    "Indian markets",
]


@app.task(name="pipeline.tasks.twitter_scraper.scrape_twitter")
def scrape_twitter() -> dict:
    """Scrape tweets matching Indian market search queries.

    WARNING: Twitter scraping is experimental and may be unreliable
    due to API limitations and rate limiting.
    """
    if not check_schema_ready():
        return {"status": "skipped", "reason": "database schema not ready"}

    logger.warning(
        "Twitter scraping is experimental and may not work reliably. "
        "API access and rate limits apply."
    )
    logger.info("Starting Twitter scrape for %d queries", len(DEFAULT_QUERIES))
    results = {}
    for query in DEFAULT_QUERIES:
        logger.info("Dispatching Twitter search for: %s", query)
        scrape_twitter_query.delay(query)
        results[query] = "dispatched"
    return results


@app.task(name="pipeline.tasks.twitter_scraper.scrape_twitter_query", bind=True)
def scrape_twitter_query(self: Task, query: str) -> dict:
    """Search and scrape tweets for a single query.

    Args:
        query: Search query string (hashtag, keyword, or cashtag).

    Returns:
        Dict with query and count of tweets scraped.
    """
    logger.info("Searching Twitter for: %s", query)

    client = TwitterClient()
    tweets = client.search_tweets(query)

    if not tweets:
        logger.info("No tweets found for query: %s", query)
        return {"query": query, "tweets_scraped": 0, "status": "twitter_unavailable"}

    tweets_inserted = 0

    with get_db() as db:
        for tweet in tweets:
            try:
                tweet_url = f"https://twitter.com/i/web/status/{tweet.get('id', '')}"

                result = db.execute(
                    text(
                        "SELECT id FROM social_sentiments WHERE post_url = :url AND platform = 'twitter'"
                    ),
                    {"url": tweet_url},
                ).fetchone()

                if result:
                    continue

                content = tweet.get("text", "")
                engagement = tweet.get("like_count", 0) + tweet.get("retweet_count", 0)

                db.execute(
                    text("""
                        INSERT INTO social_sentiments 
                        (article_id, stock_id, platform, post_url, content, sentiment_score, engagement)
                        VALUES (NULL, NULL, 'twitter', :post_url, :content, 0.0, :engagement)
                    """),
                    {
                        "post_url": tweet_url,
                        "content": content,
                        "engagement": engagement,
                    },
                )
                tweets_inserted += 1

            except Exception as e:
                logger.error(
                    "Error processing tweet %s: %s", tweet.get("id", "unknown"), str(e)
                )
                continue

    logger.info("Twitter scrape complete: %s - %d tweets", query, tweets_inserted)
    return {"query": query, "tweets_scraped": tweets_inserted, "status": "success"}
