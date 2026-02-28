from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.websocket_manager import manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


async def send_ping(websocket: WebSocket) -> None:
    """Send a ping to keep the connection alive."""
    try:
        await websocket.send_json({"type": "ping"})
    except Exception:
        pass


async def keepalive_loop(websocket: WebSocket, stop_event: asyncio.Event) -> None:
    """Send keepalive pings every 30 seconds."""
    while not stop_event.is_set():
        await asyncio.sleep(30)
        try:
            await websocket.send_json({"type": "ping"})
        except Exception:
            break


@router.websocket("/ws/feed")
async def ws_news_feed(websocket: WebSocket) -> None:
    """Live news feed WebSocket endpoint.

    - Subscribes to "feed" channel for new articles
    - Sends last 10 news articles on connect
    - Supports client messages for filter preferences
    """
    channel = "feed"
    await manager.connect(websocket, channel)
    stop_event = asyncio.Event()
    redis_task: asyncio.Task | None = None
    keepalive_task: asyncio.Task | None = None

    try:
        async for db in get_db():
            result = await db.execute(
                text("""
                    SELECT id, title, summary, url, source, published_at
                    FROM news_articles
                    ORDER BY published_at DESC
                    LIMIT 10
                """)
            )
            articles = result.fetchall()

            initial_payload = {
                "type": "initial_articles",
                "data": [
                    {
                        "id": str(a.id),
                        "title": a.title,
                        "summary": a.summary,
                        "url": a.url,
                        "source": a.source,
                        "published_at": a.published_at.isoformat()
                        if a.published_at
                        else None,
                    }
                    for a in articles
                ],
            }
            await websocket.send_json(initial_payload)
            break

        redis_task = asyncio.create_task(manager.subscribe_redis(channel, websocket))

        keepalive_task = asyncio.create_task(keepalive_loop(websocket, stop_event))

        try:
            while True:
                data = await websocket.receive_text()
                try:
                    message = json.loads(data)
                    msg_type = message.get("type")

                    if msg_type == "ping":
                        await websocket.send_json({"type": "pong"})
                    else:
                        logger.debug("Received from client: %s", message)

                except json.JSONDecodeError:
                    logger.warning("Invalid JSON from client: %s", data)

        except (WebSocketDisconnect, Exception):
            pass

    except Exception as e:
        logger.error("WebSocket error in feed: %s", e)

    finally:
        stop_event.set()
        if redis_task and not redis_task.done():
            redis_task.cancel()
        if keepalive_task and not keepalive_task.done():
            keepalive_task.cancel()
        await manager.disconnect(websocket, channel)


@router.websocket("/ws/stock/{ticker}")
async def ws_stock_updates(websocket: WebSocket, ticker: str) -> None:
    """Per-stock real-time updates WebSocket endpoint.

    - Subscribes to "stock:{ticker}" channel for updates
    - Sends latest stock data and recent sentiment on connect
    - Streams real-time updates for that ticker
    """
    channel = f"stock:{ticker.upper()}"
    await manager.connect(websocket, channel)
    stop_event = asyncio.Event()
    redis_task: asyncio.Task | None = None
    keepalive_task: asyncio.Task | None = None

    try:
        async for db in get_db():
            stock_result = await db.execute(
                text(
                    "SELECT id, ticker, sector, last_price FROM stocks WHERE ticker = :ticker"
                ),
                {"ticker": ticker.upper()},
            )
            stock = stock_result.fetchone()

            if not stock:
                await websocket.send_json(
                    {"type": "error", "message": f"Stock {ticker.upper()} not found"}
                )
                break

            sentiment_result = await db.execute(
                text("""
                    SELECT sa.sentiment_score, sa.confidence, sa.explanation, sa.analyzed_at,
                           na.title
                    FROM sentiment_analyses sa
                    JOIN article_stock_mentions asm ON sa.article_id = asm.article_id
                    JOIN news_articles na ON sa.article_id = na.id
                    WHERE asm.stock_id = :stock_id
                    ORDER BY sa.analyzed_at DESC
                    LIMIT 5
                """),
                {"stock_id": str(stock.id)},
            )
            recent_sentiments = sentiment_result.fetchall()

            initial_payload = {
                "type": "stock_data",
                "data": {
                    "stock": {
                        "id": str(stock.id),
                        "ticker": stock.ticker,
                        "sector": stock.sector,
                        "last_price": float(stock.last_price)
                        if stock.last_price
                        else None,
                    },
                    "recent_sentiments": [
                        {
                            "score": s.sentiment_score,
                            "confidence": s.confidence,
                            "explanation": s.explanation,
                            "analyzed_at": s.analyzed_at.isoformat()
                            if s.analyzed_at
                            else None,
                            "article_title": s.title,
                        }
                        for s in recent_sentiments
                    ],
                },
            }
            await websocket.send_json(initial_payload)
            break

        redis_task = asyncio.create_task(manager.subscribe_redis(channel, websocket))

        keepalive_task = asyncio.create_task(keepalive_loop(websocket, stop_event))

        try:
            while True:
                data = await websocket.receive_text()
                try:
                    message = json.loads(data)
                    msg_type = message.get("type")

                    if msg_type == "ping":
                        await websocket.send_json({"type": "pong"})
                    else:
                        logger.debug("Received from client: %s", message)

                except json.JSONDecodeError:
                    logger.warning("Invalid JSON from client: %s", data)

        except (WebSocketDisconnect, Exception):
            pass

    except Exception as e:
        logger.error("WebSocket error in stock updates: %s", e)

    finally:
        stop_event.set()
        if redis_task and not redis_task.done():
            redis_task.cancel()
        if keepalive_task and not keepalive_task.done():
            keepalive_task.cancel()
        await manager.disconnect(websocket, channel)


@router.websocket("/ws/portfolio/{portfolio_id}")
async def ws_portfolio_updates(websocket: WebSocket, portfolio_id: str) -> None:
    """Per-portfolio real-time updates WebSocket endpoint.

    - Subscribes to "portfolio:{portfolio_id}" channel for updates
    - Sends current portfolio state on connect
    - Streams updates when portfolio stocks get new sentiment/alpha data
    """
    channel = f"portfolio:{portfolio_id}"
    await manager.connect(websocket, channel)
    stop_event = asyncio.Event()
    redis_task: asyncio.Task | None = None
    keepalive_task: asyncio.Task | None = None

    try:
        async for db in get_db():
            portfolio_result = await db.execute(
                text("SELECT id, name, created_at FROM portfolios WHERE id = :id"),
                {"id": portfolio_id},
            )
            portfolio = portfolio_result.fetchone()

            if not portfolio:
                await websocket.send_json(
                    {"type": "error", "message": f"Portfolio {portfolio_id} not found"}
                )
                break

            holdings_result = await db.execute(
                text("""
                    SELECT ps.stock_id, ps.quantity, ps.avg_buy_price,
                           s.ticker, s.last_price, s.sector,
                           am.composite_score, am.signal, am.conviction
                    FROM portfolio_stocks ps
                    JOIN stocks s ON ps.stock_id = s.id
                    LEFT JOIN alpha_metrics am ON s.id = am.stock_id
                    WHERE ps.portfolio_id = :portfolio_id
                """),
                {"portfolio_id": portfolio_id},
            )
            holdings = holdings_result.fetchall()

            total_value = 0.0
            total_cost = 0.0
            holdings_data = []

            for h in holdings:
                current_price = float(h.last_price) if h.last_price else 0.0
                cost = float(h.avg_buy_price) if h.avg_buy_price else 0.0
                position_value = current_price * h.quantity
                position_cost = cost * h.quantity
                pnl = position_value - position_cost
                pnl_pct = (pnl / position_cost * 100) if position_cost > 0 else 0.0

                total_value += position_value
                total_cost += position_cost

                holdings_data.append(
                    {
                        "stock_id": str(h.stock_id),
                        "ticker": h.ticker,
                        "quantity": h.quantity,
                        "avg_buy_price": cost,
                        "current_price": current_price,
                        "value": position_value,
                        "pnl": pnl,
                        "pnl_percent": pnl_pct,
                        "sector": h.sector,
                        "alpha_score": float(h.composite_score)
                        if h.composite_score
                        else None,
                        "signal": h.signal,
                        "conviction": h.conviction,
                    }
                )

            total_pnl = total_value - total_cost
            total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0.0

            initial_payload = {
                "type": "portfolio_data",
                "data": {
                    "portfolio": {
                        "id": str(portfolio.id),
                        "name": portfolio.name,
                        "created_at": portfolio.created_at.isoformat()
                        if portfolio.created_at
                        else None,
                    },
                    "holdings": holdings_data,
                    "summary": {
                        "total_value": total_value,
                        "total_cost": total_cost,
                        "total_pnl": total_pnl,
                        "total_pnl_percent": total_pnl_pct,
                    },
                },
            }
            await websocket.send_json(initial_payload)
            break

        redis_task = asyncio.create_task(manager.subscribe_redis(channel, websocket))

        keepalive_task = asyncio.create_task(keepalive_loop(websocket, stop_event))

        try:
            while True:
                data = await websocket.receive_text()
                try:
                    message = json.loads(data)
                    msg_type = message.get("type")

                    if msg_type == "ping":
                        await websocket.send_json({"type": "pong"})
                    else:
                        logger.debug("Received from client: %s", message)

                except json.JSONDecodeError:
                    logger.warning("Invalid JSON from client: %s", data)

        except (WebSocketDisconnect, Exception):
            pass

    except Exception as e:
        logger.error("WebSocket error in portfolio updates: %s", e)

    finally:
        stop_event.set()
        if redis_task and not redis_task.done():
            redis_task.cancel()
        if keepalive_task and not keepalive_task.done():
            keepalive_task.cancel()
        await manager.disconnect(websocket, channel)
