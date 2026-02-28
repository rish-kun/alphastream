"""Metrics collection for pipeline monitoring."""

from prometheus_client import Counter, Histogram, Gauge

# Task metrics
TASK_COUNTER = Counter(
    "pipeline_tasks_total",
    "Total number of tasks executed",
    ["task_name", "status"]
)

TASK_DURATION = Histogram(
    "pipeline_task_duration_seconds",
    "Task execution duration",
    ["task_name"]
)

# Scraping metrics
ARTICLES_SCRAPED = Counter(
    "articles_scraped_total",
    "Total articles scraped",
    ["source"]
)

SCRAPER_ERRORS = Counter(
    "scraper_errors_total",
    "Total scraper errors",
    ["source", "error_type"]
)

# ML metrics
SENTIMENT_PROCESSED = Counter(
    "sentiment_processed_total",
    "Total sentiment analyses performed"
)

SENTIMENT_DURATION = Histogram(
    "sentiment_processing_duration_seconds",
    "Sentiment analysis duration"
)

# LLM metrics
LLM_REQUESTS = Counter(
    "llm_requests_total",
    "Total LLM API requests",
    ["provider", "status"]
)

LLM_DURATION = Histogram(
    "llm_request_duration_seconds",
    "LLM API request duration",
    ["provider"]
)

ACTIVE_TASKS = Gauge(
    "pipeline_active_tasks",
    "Number of currently active tasks"
)


def record_task_success(task_name: str, duration: float):
    """Record successful task execution."""
    TASK_COUNTER.labels(task_name=task_name, status="success").inc()
    TASK_DURATION.labels(task_name=task_name).observe(duration)


def record_task_failure(task_name: str, duration: float):
    """Record failed task execution."""
    TASK_COUNTER.labels(task_name=task_name, status="failure").inc()
    TASK_DURATION.labels(task_name=task_name).observe(duration)


def record_article_scraped(source: str):
    """Record scraped article."""
    ARTICLES_SCRAPED.labels(source=source).inc()


def record_scraper_error(source: str, error_type: str):
    """Record scraper error."""
    SCRAPER_ERRORS.labels(source=source, error_type=error_type).inc()
