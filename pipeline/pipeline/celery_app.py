import os
from celery import Celery
from celery.schedules import crontab

# Redis broker
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6380/0")

app = Celery(
    "alphastream",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "pipeline.tasks.rss_ingestion",
        "pipeline.tasks.web_scraper",
        "pipeline.tasks.reddit_scraper",
        "pipeline.tasks.twitter_scraper",
        "pipeline.tasks.sentiment_analysis",
        "pipeline.tasks.ticker_identification",
        "pipeline.tasks.alpha_metrics",
        "pipeline.tasks.extensive_research",
    ],
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=300,
    task_time_limit=600,
)

# Beat schedule for periodic tasks
app.conf.beat_schedule = {
    "rss-ingestion-every-10-min": {
        "task": "pipeline.tasks.rss_ingestion.fetch_all_feeds",
        "schedule": 600.0,  # 10 minutes
    },
    "full-text-scrape-every-15-min": {
        "task": "pipeline.tasks.web_scraper.scrape_pending_articles",
        "schedule": 900.0,  # 15 minutes
    },
    "reddit-scrape-every-30-min": {
        "task": "pipeline.tasks.reddit_scraper.scrape_subreddits",
        "schedule": 1800.0,  # 30 minutes
    },
    "twitter-scrape-every-30-min": {
        "task": "pipeline.tasks.twitter_scraper.scrape_twitter",
        "schedule": 1800.0,  # 30 minutes
    },
    "sentiment-analysis-every-5-min": {
        "task": "pipeline.tasks.sentiment_analysis.analyze_pending",
        "schedule": 300.0,  # 5 minutes
    },
    "alpha-computation-every-15-min": {
        "task": "pipeline.tasks.alpha_metrics.compute_all",
        "schedule": 900.0,  # 15 minutes
    },
}
