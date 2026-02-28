"""Celery task definitions for data processing pipelines."""

from celery import Celery
from celery.signals import task_failure, task_success

from pipelines.config import settings

# Initialize Celery app
celery_app = Celery(
    "alphastream",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.REDIS_URL,
    include=[
        "pipelines.scrapers.news",
        "pipelines.ml.sentiment",
        "pipelines.llm.analysis",
    ],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    worker_prefetch_multiplier=1,
)


@task_success.connect
def handle_task_success(sender=None, result=None, **kwargs):
    """Handle successful task completion."""
    print(f"Task {sender.name} completed successfully")


@task_failure.connect
def handle_task_failure(sender=None, exception=None, **kwargs):
    """Handle task failure."""
    print(f"Task {sender.name} failed: {exception}")


@celery_app.task(bind=True, max_retries=3)
def scrape_news_task(self, source: str):
    """Task to scrape news from a specific source."""
    try:
        from pipelines.scrapers.news import scrape_source
        return scrape_source(source)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=3)
def analyze_sentiment_task(self, article_id: str):
    """Task to analyze sentiment of an article."""
    try:
        from pipelines.ml.sentiment import analyze_article
        return analyze_article(article_id)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=3)
def generate_llm_analysis_task(self, article_id: str):
    """Task to generate LLM-based analysis of an article."""
    try:
        from pipelines.llm.analysis import generate_analysis
        return generate_analysis(article_id)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
