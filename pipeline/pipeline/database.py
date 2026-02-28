"""Synchronous database engine and session for Celery tasks.

Celery workers are synchronous, so we use psycopg2 (sync driver)
instead of asyncpg. The schema is managed by Alembic in the backend.
We use SQLAlchemy Core with text() for raw SQL queries to avoid
duplicating ORM models from the backend.
"""

import logging
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from pipeline.config import settings

logger = logging.getLogger(__name__)

engine = create_engine(
    settings.DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
)

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


# Required tables created by Alembic migration 001
_REQUIRED_TABLES = frozenset(
    {
        "users",
        "stocks",
        "news_articles",
        "article_stock_mentions",
        "sentiment_analyses",
        "alpha_metrics",
        "social_sentiments",
        "portfolios",
        "portfolio_stocks",
    }
)

_schema_checked: bool = False
_schema_ready: bool = False


def check_schema_ready() -> bool:
    """Return True if all required tables exist in the database.

    Caches the result after the first successful check so subsequent
    calls are free.  A failed check is retried on every call so the
    worker will recover automatically after migrations are applied.
    """
    global _schema_checked, _schema_ready

    if _schema_ready:
        return True

    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
            )
            existing = {row[0] for row in result}

        missing = _REQUIRED_TABLES - existing
        if missing:
            logger.warning(
                "Database schema not ready — missing tables: %s. "
                "Run 'cd backend && uv run alembic upgrade head' to apply migrations.",
                ", ".join(sorted(missing)),
            )
            _schema_checked = True
            _schema_ready = False
            return False

        _schema_checked = True
        _schema_ready = True
        return True
    except Exception as exc:
        logger.warning("Could not check database schema: %s", exc)
        return False


@contextmanager
def get_db():
    """Context manager that yields a sync SQLAlchemy session.

    Usage:
        with get_db() as db:
            result = db.execute(text("SELECT ..."))
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
