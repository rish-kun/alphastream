from __future__ import annotations

import logging
from typing import Annotated

from celery import Celery
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.config import settings
from app.database import get_db
from app.models.stock import Stock
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/google-news", tags=["google-news"])

_celery_app = Celery(
    "alphastream-google-news",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)


class ScrapeKeywordResponse(BaseModel):
    task_id: str
    status: str
    keyword: str
    message: str


class ScrapeStockResponse(BaseModel):
    task_id: str
    status: str
    ticker: str
    message: str


class ScrapeStatusResponse(BaseModel):
    task_id: str
    status: str
    result: dict | None = None
    error: str | None = None


@router.post("/scrape/keyword", response_model=ScrapeKeywordResponse, status_code=202)
async def scrape_news_by_keyword(
    keyword: str,
    max_results: int = 30,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> ScrapeKeywordResponse:
    """
    Trigger Google News scraping for a specific keyword.
    Called when user searches for keywords in news search.
    """
    if not keyword or not keyword.strip():
        raise HTTPException(status_code=400, detail="Keyword cannot be empty")

    keyword = keyword.strip()

    task = _celery_app.send_task(
        "pipeline.tasks.google_news_scraper.scrape_google_news_by_keyword",
        kwargs={
            "keyword": keyword,
            "user_id": str(current_user.id),
            "max_results": max_results,
        },
    )

    return ScrapeKeywordResponse(
        task_id=task.id,
        status="queued",
        keyword=keyword,
        message=f"Scraping Google News for '{keyword}'",
    )


@router.post(
    "/scrape/stock/{ticker}", response_model=ScrapeStockResponse, status_code=202
)
async def scrape_news_by_stock(
    ticker: str,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> ScrapeStockResponse:
    """
    Trigger Google News scraping for a specific stock ticker.
    Called when user searches or selects a specific stock.
    """
    ticker = ticker.upper().strip()

    result = await db.execute(select(Stock).where(Stock.ticker == ticker))
    stock = result.scalar_one_or_none()
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")

    task = _celery_app.send_task(
        "pipeline.tasks.google_news_scraper.scrape_single_ticker",
        kwargs={
            "ticker": ticker,
            "user_id": str(current_user.id),
        },
    )

    return ScrapeStockResponse(
        task_id=task.id,
        status="queued",
        ticker=ticker,
        message=f"Scraping Google News for {ticker}",
    )


@router.get("/scrape/status/{task_id}", response_model=ScrapeStatusResponse)
async def get_scrape_status(
    task_id: str,
    current_user: Annotated[User, Depends(get_current_user)] = None,
) -> ScrapeStatusResponse:
    """
    Get the status of a scraping task.
    """
    result = _celery_app.AsyncResult(task_id)
    state = result.state

    if state == "PENDING":
        return ScrapeStatusResponse(task_id=task_id, status=state)

    if state == "FAILURE":
        return ScrapeStatusResponse(
            task_id=task_id,
            status=state,
            error=str(result.info),
        )

    return ScrapeStatusResponse(
        task_id=task_id,
        status=state,
        result=result.result if result.ready() else None,
    )
