from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.portfolio import (
    PortfolioCreate,
    PortfolioResponse,
    PortfolioStockAdd,
    PortfolioUpdate,
)
from app.services.portfolio_service import PortfolioService

router = APIRouter(prefix="/portfolios", tags=["portfolios"])


@router.get("/", response_model=list[PortfolioResponse])
async def list_portfolios(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> list[PortfolioResponse]:
    service = PortfolioService(db)
    return await service.list_portfolios(current_user.id)


@router.post("/", response_model=PortfolioResponse, status_code=201)
async def create_portfolio(
    data: PortfolioCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> PortfolioResponse:
    service = PortfolioService(db)
    return await service.create_portfolio(current_user.id, data)


@router.put("/{id}", response_model=PortfolioResponse)
async def update_portfolio(
    id: uuid.UUID,
    data: PortfolioUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> PortfolioResponse:
    service = PortfolioService(db)
    return await service.update_portfolio(current_user.id, id, data)


@router.delete("/{id}", status_code=204)
async def delete_portfolio(
    id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> None:
    service = PortfolioService(db)
    await service.delete_portfolio(current_user.id, id)


@router.post("/{id}/stocks", response_model=dict, status_code=201)
async def add_stock(
    id: uuid.UUID,
    data: PortfolioStockAdd,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> dict:
    service = PortfolioService(db)
    return await service.add_stock(
        current_user.id,
        id,
        data.ticker,
        data.quantity,
        data.avg_buy_price,
    )


@router.delete("/{id}/stocks/{ticker}", status_code=204)
async def remove_stock(
    id: uuid.UUID,
    ticker: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> None:
    service = PortfolioService(db)
    await service.remove_stock(current_user.id, id, ticker)


@router.get("/{id}/news", response_model=dict)
async def get_portfolio_news(
    id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> dict:
    service = PortfolioService(db)
    return await service.get_portfolio_news(current_user.id, id)


@router.get("/{id}/alpha", response_model=dict)
async def get_portfolio_alpha(
    id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> dict:
    service = PortfolioService(db)
    return await service.get_portfolio_alpha(current_user.id, id)
