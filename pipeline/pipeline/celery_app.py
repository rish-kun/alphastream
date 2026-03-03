import multiprocessing
import os
from celery import Celery
from celery.schedules import crontab

from pipeline.tasks.prioritized_analysis import analyze_top_articles

if multiprocessing.get_start_method(allow_none=True) is None:
    multiprocessing.set_start_method("spawn", force=True)

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
        "pipeline.tasks.google_news_scraper",
        "pipeline.tasks.sentiment_analysis",
        "pipeline.tasks.ticker_identification",
        "pipeline.tasks.alpha_metrics",
        "pipeline.tasks.extensive_research",
        "pipeline.tasks.prioritized_analysis",
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
    worker_pool="prefork",
    worker_max_tasks_per_child=50,
    worker_max_memory_per_child=524288,
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
    task_routes={
        "pipeline.tasks.prioritized_analysis.analyze_top_articles": {
            "queue": "high_priority"
        },
        "pipeline.tasks.sentiment_analysis.analyze_article_sentiment": {
            "queue": "sentiment"
        },
        "pipeline.tasks.google_news_scraper.*": {"queue": "google_news"},
    },
    task_default_queue="celery",
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
    "google-news-scrape-every-20-min": {
        "task": "pipeline.tasks.google_news_scraper.scrape_google_news",
        "schedule": 1200.0,  # 20 minutes
        "kwargs": {"stock_tickers": None},  # Will fetch from DB
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


# Run worker with multiple queues (high priority first):
# celery -A pipeline.celery_app worker -Q high_priority,sentiment,google_news,celery -l info

# Run separate workers for different concerns:
# celery -A pipeline.celery_app worker -Q high_priority -l info -n high-priority-worker@%h
# celery -A pipeline.celery_app worker -Q sentiment -l info -n sentiment-worker@%h
# celery -A pipeline.celery_app worker -Q google_news -l info -n google-news-worker@%h
# celery -A pipeline.celery_app worker -Q celery -l info -n default-worker@%h
