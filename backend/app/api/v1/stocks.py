from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.stock import Stock
from app.schemas.stock import StockDetail, StockSearchResponse
from app.services.stock_service import StockService

router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("/search", response_model=StockSearchResponse)
async def search_stocks(
    q: Annotated[str, Query(description="Search query")],
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> StockSearchResponse:
    service = StockService(db)
    return await service.search_stocks(q, limit)


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


@router.get("/{ticker}/news", response_model=dict)
async def get_stock_news(
    ticker: str,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 20,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> dict:
    service = StockService(db)
    return await service.get_stock_news(ticker, page, page_size)


@router.get("/{ticker}/alpha", response_model=dict)
async def get_stock_alpha(
    ticker: str,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> dict:
    service = StockService(db)
    return await service.get_stock_alpha(ticker)
