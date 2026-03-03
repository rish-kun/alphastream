"""Debug endpoints for testing the deep research pipeline.

This module provides debug endpoints to test the research functionality
without requiring full authentication. These endpoints should be used
only for development/testing purposes.

Add to router with:
    from app.api.v1.research_debug import router as research_debug_router
    api_router.include_router(research_debug_router, prefix="/research-debug")
"""

from __future__ import annotations

import logging
from datetime import datetime, UTC
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.user import User
from app.models.news import NewsArticle

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/research-debug", tags=["research-debug"])


def mask_api_key(key: str, visible_chars: int = 4) -> str:
    """Mask an API key for safe display."""
    if not key:
        return "(not configured)"
    if len(key) <= visible_chars * 2:
        return f"{key[:2]}...{key[-2:]}"
    return f"{key[:visible_chars]}...{key[-visible_chars:]}"


class DebugConfigResponse(BaseModel):
    """Response model for debug configuration status."""

    api_keys: dict[str, str]
    database: dict[str, Any]
    scrapers: dict[str, bool]


@router.get("/config", response_model=DebugConfigResponse)
async def get_debug_config():
    """Get debug information about API keys and configuration.

    This endpoint shows which API keys are configured (masked) and
    the database connection status.
    """
    from pipeline.config import settings as pipeline_settings

    api_keys = {
        "FIRECRAWL_API_KEY": mask_api_key(pipeline_settings.FIRECRAWL_API_KEY),
        "THUNDERBIT_API_KEY": mask_api_key(pipeline_settings.THUNDERBIT_API_KEY),
        "BROWSEAI_API_KEY": mask_api_key(pipeline_settings.BROWSEAI_API_KEY),
        "BROWSEAI_TEAM_ID": pipeline_settings.BROWSEAI_TEAM_ID or "(not configured)",
        "BROWSEAI_DEFAULT_ROBOT_ID": pipeline_settings.BROWSEAI_DEFAULT_ROBOT_ID
        or "(not configured)",
    }

    database_status = {
        "configured": True,
        "url": f"postgresql+psycopg2://...@{pipeline_settings.DATABASE_URL.split('@')[-1]}"
        if "@" in pipeline_settings.DATABASE_URL
        else "local",
    }

    try:
        from pipeline.database import check_schema_ready

        database_status["schema_ready"] = check_schema_ready()
    except Exception as e:
        database_status["schema_ready"] = False
        database_status["error"] = str(e)

    scrapers = {
        "firecrawl": bool(pipeline_settings.FIRECRAWL_API_KEY),
        "thunderbit": bool(pipeline_settings.THUNDERBIT_API_KEY),
        "browseai": bool(pipeline_settings.BROWSEAI_API_KEY),
    }

    return DebugConfigResponse(
        api_keys=api_keys,
        database=database_status,
        scrapers=scrapers,
    )


class ScraperTestRequest(BaseModel):
    """Request model for scraper test."""

    topic: str = Field(..., min_length=1, max_length=200)
    limit: int = Field(default=5, ge=1, le=20)


class ScraperTestResponse(BaseModel):
    """Response model for scraper test results."""

    scraper: str
    results_count: int
    results: list[dict[str, Any]]
    error: str | None = None


@router.post("/test-scraper/{scraper_name}", response_model=ScraperTestResponse)
async def test_scraper(scraper_name: str, body: ScraperTestRequest):
    """Test a specific scraper with a given topic.

    Args:
        scraper_name: One of 'firecrawl', 'thunderbit', 'browseai'
        body: Request body with topic and limit
    """
    scraper_name = scraper_name.lower()

    if scraper_name not in ("firecrawl", "thunderbit", "browseai"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid scraper: {scraper_name}. Must be one of: firecrawl, thunderbit, browseai",
        )

    logger.info(f"Testing {scraper_name} with topic: {body.topic}")

    try:
        if scraper_name == "firecrawl":
            from pipeline.scrapers.firecrawl_client import FirecrawlClient

            client = FirecrawlClient()
            results = client.search_indian_financial_news(body.topic, limit=body.limit)

        elif scraper_name == "thunderbit":
            from pipeline.scrapers.thunderbit_client import ThunderbitClient

            client = ThunderbitClient()
            results = client.search_and_scrape(body.topic, limit=body.limit)

        else:  # browseai
            from pipeline.scrapers.browseai_client import BrowseAIClient

            client = BrowseAIClient()
            results = client.search_financial_news(body.topic)

        return ScraperTestResponse(
            scraper=scraper_name,
            results_count=len(results),
            results=results,
            error=None,
        )

    except Exception as e:
        logger.error(f"Scraper test error: {str(e)}", exc_info=True)
        return ScraperTestResponse(
            scraper=scraper_name,
            results_count=0,
            results=[],
            error=str(e),
        )


@router.post("/test-all-scrapers")
async def test_all_scrapers(body: ScraperTestRequest):
    """Test all configured scrapers with a given topic.

    Returns results from Firecrawl, Thunderbit, and Browse.ai (if configured).
    """
    logger.info(f"Testing all scrapers with topic: {body.topic}")

    results: dict[str, Any] = {
        "topic": body.topic,
        "scrapers": {},
        "combined_count": 0,
    }

    scraper_list = [
        ("firecrawl", "FirecrawlClient", "search_indian_financial_news"),
        ("thunderbit", "ThunderbitClient", "search_and_scrape"),
        ("browseai", "BrowseAIClient", "search_financial_news"),
    ]

    for scraper_name, client_class, method_name in scraper_list:
        try:
            if scraper_name == "firecrawl":
                from pipeline.scrapers.firecrawl_client import FirecrawlClient

                client = FirecrawlClient()
                articles = client.search_indian_financial_news(
                    body.topic, limit=body.limit
                )
            elif scraper_name == "thunderbit":
                from pipeline.scrapers.thunderbit_client import ThunderbitClient

                client = ThunderbitClient()
                articles = client.search_and_scrape(body.topic, limit=body.limit)
            else:
                from pipeline.scrapers.browseai_client import BrowseAIClient

                client = BrowseAIClient()
                articles = client.search_financial_news(body.topic)

            results["scrapers"][scraper_name] = {
                "status": "success",
                "count": len(articles),
                "articles": articles,
            }
            results["combined_count"] += len(articles)

        except Exception as e:
            results["scrapers"][scraper_name] = {
                "status": "error",
                "count": 0,
                "error": str(e),
                "articles": [],
            }
            logger.warning(f"{scraper_name} test failed: {str(e)}")

    return results


class StoreArticlesRequest(BaseModel):
    """Request model for storing articles."""

    articles: list[dict[str, Any]]
    source_query: str


class StoreArticlesResponse(BaseModel):
    """Response model for stored articles."""

    stored_count: int
    article_ids: list[str]
    source_query: str


@router.post("/store-articles", response_model=StoreArticlesResponse)
async def store_articles(body: StoreArticlesRequest):
    """Store research articles in the database.

    This endpoint tests the _store_research_articles function
    with provided article data.
    """
    if not body.articles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No articles provided"
        )

    logger.info(f"Storing {len(body.articles)} articles for query: {body.source_query}")

    try:
        from pipeline.tasks.extensive_research import _store_research_articles

        new_count, article_ids = _store_research_articles(
            body.articles, source_query=body.source_query
        )

        return StoreArticlesResponse(
            stored_count=new_count,
            article_ids=article_ids,
            source_query=body.source_query,
        )

    except Exception as e:
        logger.error(f"Store articles error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store articles: {str(e)}",
        )


class DatabaseStatusResponse(BaseModel):
    """Response model for database status."""

    connection: bool
    schema_ready: bool
    tables: list[str]
    article_count: int


@router.get("/database-status", response_model=DatabaseStatusResponse)
async def get_database_status(db: AsyncSession = Depends(get_db)):
    """Get database connection and schema status."""
    try:
        result = await db.execute(text("SELECT 1"))
        connection_ok = result.scalar() == 1
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database connection failed: {str(e)}",
        )

    try:
        result = await db.execute(
            text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
        )
        tables = [row[0] for row in result.fetchall()]
    except Exception:
        tables = []

    try:
        result = await db.execute(text("SELECT COUNT(*) FROM news_articles"))
        article_count = result.scalar() or 0
    except Exception:
        article_count = 0

    schema_ready = "news_articles" in tables

    return DatabaseStatusResponse(
        connection=connection_ok,
        schema_ready=schema_ready,
        tables=tables,
        article_count=article_count,
    )


class RecentArticlesResponse(BaseModel):
    """Response model for recent articles."""

    articles: list[dict[str, Any]]
    count: int


@router.get("/recent-articles", response_model=RecentArticlesResponse)
async def get_recent_articles(
    limit: int = Query(default=10, ge=1, le=50),
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Get recent news articles from the database.

    Args:
        limit: Maximum number of articles to return
        category: Optional filter by category
    """
    try:
        query = (
            select(NewsArticle).order_by(NewsArticle.published_at.desc()).limit(limit)
        )

        if category:
            query = query.where(NewsArticle.category == category)

        result = await db.execute(query)
        articles = result.scalars().all()

        article_dicts = []
        for article in articles:
            article_dicts.append(
                {
                    "id": str(article.id),
                    "title": article.title,
                    "url": article.url,
                    "source": article.source,
                    "published_at": article.published_at.isoformat()
                    if article.published_at
                    else None,
                    "scraped_at": article.scraped_at.isoformat()
                    if article.scraped_at
                    else None,
                    "category": article.category,
                    "summary": article.summary[:100] + "..."
                    if article.summary and len(article.summary) > 100
                    else article.summary,
                }
            )

        return RecentArticlesResponse(
            articles=article_dicts,
            count=len(article_dicts),
        )

    except Exception as e:
        logger.error(f"Error fetching recent articles: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch articles: {str(e)}",
        )
