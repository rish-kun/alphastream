from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import WebSocket
from redis.asyncio import Redis

from app.config import settings

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and message broadcasting.

    Supports channel-based subscriptions and broadcasting.
    Integrates with Redis pub/sub for multi-process deployments.
    """

    def __init__(self) -> None:
        self.active_connections: dict[str, set[WebSocket]] = {}
        self._lock = asyncio.Lock()
        self._redis: Redis | None = None
        self._redis_tasks: dict[str, asyncio.Task] = {}

    async def _get_redis(self) -> Redis:
        """Get or create Redis connection."""
        if self._redis is None:
            self._redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        return self._redis

    async def connect(self, websocket: WebSocket, channel: str) -> None:
        """Accept a WebSocket connection and subscribe to a channel."""
        await websocket.accept()
        async with self._lock:
            if channel not in self.active_connections:
                self.active_connections[channel] = set()
            self.active_connections[channel].add(websocket)
        logger.info("WebSocket connected to channel: %s", channel)

    async def disconnect(self, websocket: WebSocket, channel: str) -> None:
        """Remove a WebSocket connection from a channel."""
        async with self._lock:
            if channel in self.active_connections:
                self.active_connections[channel].discard(websocket)
                if not self.active_connections[channel]:
                    del self.active_connections[channel]
        logger.info("WebSocket disconnected from channel: %s", channel)

    async def subscribe(self, websocket: WebSocket, channel: str) -> None:
        """Subscribe a connected WebSocket to an additional channel."""
        async with self._lock:
            if channel not in self.active_connections:
                self.active_connections[channel] = set()
            self.active_connections[channel].add(websocket)

    async def unsubscribe(self, websocket: WebSocket, channel: str) -> None:
        """Unsubscribe a WebSocket from a channel."""
        async with self._lock:
            if channel in self.active_connections:
                self.active_connections[channel].discard(websocket)
                if not self.active_connections[channel]:
                    del self.active_connections[channel]

    async def broadcast(self, channel: str, message: dict[str, Any]) -> None:
        """Broadcast a JSON message to all connections in a channel."""
        connections = self.active_connections.get(channel, set()).copy()
        disconnected: list[WebSocket] = []

        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)

        for ws in disconnected:
            await self.disconnect(ws, channel)

    async def send_personal(
        self, websocket: WebSocket, message: dict[str, Any]
    ) -> None:
        """Send a JSON message to a specific WebSocket connection."""
        try:
            await websocket.send_json(message)
        except Exception:
            pass

    async def subscribe_redis(self, channel: str, websocket: WebSocket) -> None:
        """Background task that subscribes to Redis pub/sub channel and forwards messages."""
        try:
            redis = await self._get_redis()
            pubsub = redis.pubsub()
            await pubsub.subscribe(channel)

            logger.info("Redis subscription started for channel: %s", channel)

            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        await websocket.send_json(data)
                    except json.JSONDecodeError:
                        logger.warning(
                            "Invalid JSON in Redis message: %s", message["data"]
                        )
                    except Exception as e:
                        logger.error("Error sending Redis message to WebSocket: %s", e)
                        break

        except asyncio.CancelledError:
            logger.info("Redis subscription cancelled for channel: %s", channel)
        except Exception as e:
            logger.error("Redis subscription error for channel %s: %s", channel, e)

    async def start_redis_listener(self, channel: str) -> asyncio.Task:
        """Start a background task for Redis pub/sub listening for a channel."""
        if channel in self._redis_tasks:
            return self._redis_tasks[channel]

        async def _listen():
            try:
                redis = await self._get_redis()
                pubsub = redis.pubsub()
                await pubsub.subscribe(channel)

                logger.info("Redis listener started for channel: %s", channel)

                async for message in pubsub.listen():
                    if message["type"] == "message":
                        try:
                            data = json.loads(message["data"])
                            await self.broadcast(channel, data)
                        except json.JSONDecodeError:
                            logger.warning(
                                "Invalid JSON in Redis message: %s", message["data"]
                            )
                        except Exception as e:
                            logger.error("Error broadcasting Redis message: %s", e)

            except asyncio.CancelledError:
                logger.info("Redis listener cancelled for channel: %s", channel)
            except Exception as e:
                logger.error("Redis listener error for channel %s: %s", channel, e)

        task = asyncio.create_task(_listen())
        self._redis_tasks[channel] = task
        return task

    async def publish_to_redis(self, channel: str, data: dict[str, Any]) -> None:
        """Publish a message to Redis pub/sub for cross-process broadcasting."""
        try:
            redis = await self._get_redis()
            await redis.publish(channel, json.dumps(data))
            logger.debug("Published to Redis channel: %s", channel)
        except Exception as e:
            logger.error("Failed to publish to Redis channel %s: %s", channel, e)

    async def cleanup(self) -> None:
        """Clean up Redis connections and tasks."""
        for task in self._redis_tasks.values():
            task.cancel()
        self._redis_tasks.clear()

        if self._redis:
            await self._redis.close()
            self._redis = None


manager = ConnectionManager()
