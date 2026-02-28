"""Reddit scraping task for Indian finance subreddits."""

import logging
from datetime import datetime, timezone

from celery import Task
from sqlalchemy import text

from pipeline.celery_app import app
from pipeline.database import get_db
from pipeline.scrapers.reddit_client import RedditClient
from pipeline.tasks.sentiment_analysis import analyze_article
from pipeline.utils.deduplication import compute_content_hash

logger = logging.getLogger(__name__)

TARGET_SUBREDDITS = [
    "IndianStreetBets",
    "IndiaInvestments",
    "DalalStreetTalks",
]


@app.task(name="pipeline.tasks.reddit_scraper.scrape_subreddits")
def scrape_subreddits() -> dict:
    """Scrape hot posts from all target Indian finance subreddits.

    Dispatches individual subreddit scrape tasks for parallel processing.
    """
    logger.info("Starting Reddit scrape for %d subreddits", len(TARGET_SUBREDDITS))
    results = {}
    for subreddit in TARGET_SUBREDDITS:
        logger.info("Dispatching scrape for r/%s", subreddit)
        scrape_subreddit.delay(subreddit, limit=25)
        results[subreddit] = "dispatched"
    return results


@app.task(name="pipeline.tasks.reddit_scraper.scrape_subreddit", bind=True)
def scrape_subreddit(self: Task, subreddit_name: str, limit: int = 25) -> dict:
    """Scrape hot posts and comments from a single subreddit.

    Args:
        subreddit_name: Name of the subreddit (without r/ prefix).
        limit: Maximum number of hot posts to fetch.

    Returns:
        Dict with subreddit name and count of posts scraped.
    """
    logger.info("Scraping r/%s (limit=%d)", subreddit_name, limit)

    client = RedditClient()
    posts = client.get_hot_posts(subreddit_name, limit=limit)

    if not posts:
        logger.info("No posts fetched from r/%s", subreddit_name)
        return {"subreddit": subreddit_name, "posts_scraped": 0}

    posts_inserted = 0
    articles_created = 0

    with get_db() as db:
        for post in posts:
            try:
                post_url = post.get("url", "")
                if not post_url:
                    continue

                result = db.execute(
                    text(
                        "SELECT id FROM social_sentiments WHERE post_url = :url AND platform = 'reddit'"
                    ),
                    {"url": post_url},
                ).fetchone()

                if result:
                    continue

                content = f"{post.get('title', '')} {post.get('text', '')}".strip()
                engagement = post.get("score", 0) + post.get("num_comments", 0)

                db.execute(
                    text("""
                        INSERT INTO social_sentiments 
                        (article_id, stock_id, platform, post_url, content, sentiment_score, engagement)
                        VALUES (NULL, NULL, 'reddit', :post_url, :content, 0.0, :engagement)
                    """),
                    {
                        "post_url": post_url,
                        "content": content,
                        "engagement": engagement,
                    },
                )
                posts_inserted += 1

                if len(post.get("text", "")) > 100:
                    content_hash = compute_content_hash(
                        post.get("title", "") + post.get("text", "")
                    )
                    published_at = datetime.fromtimestamp(
                        post.get("created_utc", 0), tz=timezone.utc
                    )

                    db.execute(
                        text("""
                            INSERT INTO news_articles 
                            (title, summary, full_text, url, source, published_at, content_hash, category)
                            VALUES (:title, :summary, :full_text, :url, 'reddit', :published_at, :content_hash, 'reddit')
                            ON CONFLICT (url) DO NOTHING
                        """),
                        {
                            "title": post.get("title", ""),
                            "summary": post.get("text", "")[:500],
                            "full_text": post.get("text", ""),
                            "url": post_url,
                            "published_at": published_at,
                            "content_hash": content_hash,
                        },
                    )

                    article_result = db.execute(
                        text("SELECT id FROM news_articles WHERE url = :url"),
                        {"url": post_url},
                    ).fetchone()

                    if article_result:
                        articles_created += 1
                        article_id = article_result[0]
                        analyze_article.delay(article_id)

            except Exception as e:
                logger.error(
                    "Error processing post %s: %s", post.get("id", "unknown"), str(e)
                )
                continue

    logger.info(
        "Reddit scrape complete: r/%s - %d posts, %d articles",
        subreddit_name,
        posts_inserted,
        articles_created,
    )
    return {"subreddit": subreddit_name, "posts_scraped": posts_inserted}
