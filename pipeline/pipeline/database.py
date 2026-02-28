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
