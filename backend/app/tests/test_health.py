"""Tests for the health endpoint."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


class TestHealthEndpoint:
    async def test_health_check(self, client: AsyncClient):
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["service"] == "alphastream-backend"
        assert data["version"] == "0.1.0"
        assert "timestamp" in data

    async def test_health_check_returns_iso_timestamp(self, client: AsyncClient):
        resp = await client.get("/api/v1/health")
        data = resp.json()
        # Should be a valid ISO format timestamp
        assert "T" in data["timestamp"]
