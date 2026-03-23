"""Twitter/X scraping task (experimental)."""

import logging

from celery import Task
from sqlalchemy import text, bindparam

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
        tweet_urls = []
        tweet_data = {}
        for tweet in tweets:
            try:
                tweet_id = tweet.get("id", "")
                if not tweet_id:
                    continue
                tweet_url = f"https://twitter.com/i/web/status/{tweet_id}"

                # Deduplicate intra-batch: if we already saw this URL in the current batch, skip it
                if tweet_url not in tweet_data:
                    tweet_urls.append(tweet_url)
                    tweet_data[tweet_url] = tweet
            except Exception as e:
                logger.error("Error formatting tweet data: %s", str(e))
                continue

        existing_urls = set()
        bulk_query_success = False

        if tweet_urls:
            try:
                # Use a single query to find all existing URLs using standard IN clause with expanding bindparam
                stmt = text(
                    "SELECT post_url FROM social_sentiments WHERE post_url IN :urls AND platform = 'twitter'"
                ).bindparams(bindparam("urls", expanding=True))

                results = db.execute(
                    stmt,
                    {"urls": tuple(tweet_urls)},
                ).fetchall()
                existing_urls = {row[0] for row in results}
                bulk_query_success = True
            except Exception as e:
                logger.error("Error querying existing tweets: %s", str(e))
                # Fallback to the original row-by-row behavior if the bulk query fails

        if bulk_query_success:
            insert_values = []
            for url in tweet_urls:
                if url in existing_urls:
                    continue

                tweet = tweet_data[url]
                try:
                    content = tweet.get("text", "")
                    engagement = tweet.get("like_count", 0) + tweet.get(
                        "retweet_count", 0
                    )

                    insert_values.append(
                        {
                            "post_url": url,
                            "content": content,
                            "engagement": engagement,
                        }
                    )
                except Exception as e:
                    logger.error(
                        "Error processing tweet %s: %s",
                        tweet.get("id", "unknown"),
                        str(e),
                    )
                    continue

            if insert_values:
                try:
                    # Bulk insert missing tweets
                    db.execute(
                        text("""
                            INSERT INTO social_sentiments
                            (article_id, stock_id, platform, post_url, content, sentiment_score, engagement)
                            VALUES (NULL, NULL, 'twitter', :post_url, :content, 0.0, :engagement)
                        """),
                        insert_values,
                    )
                    tweets_inserted = len(insert_values)
                except Exception as e:
                    logger.error(
                        "Bulk insert failed, falling back to individual inserts: %s",
                        str(e),
                    )
                    # Fallback to single inserts to preserve row-level isolation
                    for val in insert_values:
                        try:
                            db.execute(
                                text("""
                                    INSERT INTO social_sentiments
                                    (article_id, stock_id, platform, post_url, content, sentiment_score, engagement)
                                    VALUES (NULL, NULL, 'twitter', :post_url, :content, 0.0, :engagement)
                                """),
                                val,
                            )
                            tweets_inserted += 1
                        except Exception as inner_e:
                            logger.error(
                                "Error inserting tweet %s: %s",
                                val["post_url"],
                                str(inner_e),
                            )
        else:
            # Fallback behavior: original N+1 check and insert
            for url in tweet_urls:
                tweet = tweet_data[url]
                try:
                    result = db.execute(
                        text(
                            "SELECT id FROM social_sentiments WHERE post_url = :url AND platform = 'twitter'"
                        ),
                        {"url": url},
                    ).fetchone()

                    if result:
                        continue

                    content = tweet.get("text", "")
                    engagement = tweet.get("like_count", 0) + tweet.get(
                        "retweet_count", 0
                    )

                    db.execute(
                        text("""
                            INSERT INTO social_sentiments
                            (article_id, stock_id, platform, post_url, content, sentiment_score, engagement)
                            VALUES (NULL, NULL, 'twitter', :post_url, :content, 0.0, :engagement)
                        """),
                        {
                            "post_url": url,
                            "content": content,
                            "engagement": engagement,
                        },
                    )
                    tweets_inserted += 1

                except Exception as e:
                    logger.error(
                        "Error processing tweet %s: %s",
                        tweet.get("id", "unknown"),
                        str(e),
                    )
                    continue

    logger.info("Twitter scrape complete: %s - %d tweets", query, tweets_inserted)
    return {"query": query, "tweets_scraped": tweets_inserted, "status": "success"}
