from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.stock import Stock
from app.schemas.stock import StockDetail, StockNewsResponse, StockSearchResponse
from app.services.stock_service import StockService

router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("/search", response_model=StockSearchResponse)
async def search_stocks(
    q: Annotated[str | None, Query(description="Search query")] = None,
    sector: Annotated[str | None, Query(description="Filter by sector")] = None,
    industry: Annotated[str | None, Query(description="Filter by industry")] = None,
    min_price: Annotated[
        float | None, Query(description="Minimum stock price", ge=0)
    ] = None,
    max_price: Annotated[
        float | None, Query(description="Maximum stock price", ge=0)
    ] = None,
    min_market_cap: Annotated[
        int | None, Query(description="Minimum market cap", ge=0)
    ] = None,
    max_market_cap: Annotated[
        int | None, Query(description="Maximum market cap", ge=0)
    ] = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> StockSearchResponse:
    service = StockService(db)
    return await service.search_stocks(
        query=q,
        limit=limit,
        sector=sector,
        industry=industry,
        min_price=min_price,
        max_price=max_price,
        min_market_cap=min_market_cap,
        max_market_cap=max_market_cap,
    )


@router.get("/sectors", response_model=list[str])
async def get_sectors(
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> list[str]:
    stmt = (
        select(Stock.sector)
        .distinct()
        .where(Stock.sector.isnot(None))
        .order_by(Stock.sector)
    )
    result = await db.execute(stmt)
    sectors = [row[0] for row in result.all()]
    return sectors


@router.get("/{ticker}", response_model=StockDetail)
async def get_stock(
    ticker: str,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> StockDetail:
    service = StockService(db)
    return await service.get_stock(ticker)


@router.get("/{ticker}/news", response_model=StockNewsResponse)
async def get_stock_news(
    ticker: str,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 20,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> StockNewsResponse:
    service = StockService(db)
    return await service.get_stock_news(ticker, page, page_size)


@router.get("/{ticker}/alpha", response_model=dict)
async def get_stock_alpha(
    ticker: str,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> dict:
    service = StockService(db)
    return await service.get_stock_alpha(ticker)
