"""Startup seeder: triggers RSS ingestion and sentiment analysis once on boot.

This script is run as a one-shot Docker service (restart: no) that fires
the pipeline tasks immediately so the app has data on first launch, rather
than waiting for the first beat schedule run (up to 10 minutes later).

Sequence:
  1. Wait for the Celery worker to be reachable via the broker.
  2. Send fetch_all_feeds task → dispatches per-feed tasks to the worker.
  3. Wait a few seconds, then send analyze_pending → queues sentiment analysis
     for any articles already scraped and stored in the DB.
  4. Exit cleanly.
"""

import logging
import os
import sys
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [startup-seed] %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://alphastream-redis:6379/0")

# How long to wait for the Celery worker to be ready (seconds)
WORKER_READY_TIMEOUT = 120
# How long to sleep between the RSS dispatch and sentiment dispatch
SENTIMENT_DELAY = 15


def wait_for_worker(timeout: int) -> bool:
    """Ping the broker until at least one worker is available."""
    from pipeline.celery_app import app as celery_app

    logger.info("Waiting for Celery worker to be available (timeout=%ds)…", timeout)
    deadline = time.time() + timeout
    interval = 5

    while time.time() < deadline:
        try:
            # inspect().ping() returns {} when no workers are up
            response = celery_app.control.inspect(timeout=3).ping()
            if response:
                logger.info("Celery worker ready: %s", list(response.keys()))
                return True
        except Exception as exc:
            logger.debug("Worker ping failed: %s", exc)
        logger.info("No workers yet, retrying in %ds…", interval)
        time.sleep(interval)

    logger.warning("Timed out waiting for Celery worker after %ds.", timeout)
    return False


def main() -> None:
    logger.info("=== AlphaStream startup seed BEGIN ===")

    # ── 1. Wait for a worker to be alive ──────────────────────────────────────
    worker_ready = wait_for_worker(WORKER_READY_TIMEOUT)
    if not worker_ready:
        # Worker didn't appear in time — send tasks anyway (they'll be queued
        # in Redis and processed as soon as the worker comes up).
        logger.warning(
            "Proceeding with task dispatch even though no worker was detected."
        )

    # ── 2. Trigger all RSS feeds ───────────────────────────────────────────────
    logger.info("Dispatching fetch_all_feeds…")
    try:
        from pipeline.celery_app import app as celery_app

        result = celery_app.send_task("pipeline.tasks.rss_ingestion.fetch_all_feeds")
        logger.info("fetch_all_feeds dispatched (task_id=%s)", result.id)
    except Exception as exc:
        logger.error("Failed to dispatch fetch_all_feeds: %s", exc)
        sys.exit(1)

    # ── 3. Brief pause so feed tasks can start writing articles to the DB ─────
    logger.info(
        "Waiting %ds before dispatching sentiment analysis…", SENTIMENT_DELAY
    )
    time.sleep(SENTIMENT_DELAY)

    # ── 4. Trigger ticker identification for any articles already in DB ────────
    logger.info("Dispatching identify_tickers_pending…")
    try:
        celery_app.send_task(
            "pipeline.tasks.ticker_identification.identify_tickers_pending"
        )
        logger.info("identify_tickers_pending dispatched")
    except Exception as exc:
        logger.warning("Failed to dispatch identify_tickers_pending: %s", exc)

    # ── 5. Trigger sentiment analysis ─────────────────────────────────────────
    logger.info("Dispatching analyze_pending…")
    try:
        result2 = celery_app.send_task(
            "pipeline.tasks.sentiment_analysis.analyze_pending"
        )
        logger.info("analyze_pending dispatched (task_id=%s)", result2.id)
    except Exception as exc:
        logger.error("Failed to dispatch analyze_pending: %s", exc)

    logger.info("=== AlphaStream startup seed DONE — tasks are queued ===")


if __name__ == "__main__":
    main()
