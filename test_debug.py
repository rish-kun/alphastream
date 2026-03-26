import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock
from app.tests.conftest import MockResult
import asyncio

async def run():
    mr = MockResult(data=[("Banking & Finance", "HDFCBANK"), ("Banking & Finance", "ICICIBANK")])
    for row in mr.all():
        print(row)
        print(type(row))
        try:
            print(row.sector)
        except AttributeError:
            print("No sector attr")
        print(row[0])

asyncio.run(run())
