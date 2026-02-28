from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.news import router as news_router
from app.api.v1.portfolio import router as portfolio_router
from app.api.v1.research import router as research_router
from app.api.v1.sentiment import router as sentiment_router
from app.api.v1.stocks import router as stocks_router
from app.api.v1.websocket import router as websocket_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(stocks_router)
api_router.include_router(news_router)
api_router.include_router(portfolio_router)
api_router.include_router(research_router)
api_router.include_router(sentiment_router)
api_router.include_router(websocket_router)
