import asyncio
from unittest.mock import AsyncMock

async def test():
    db = AsyncMock()
    # Mocks simulate the same un-awaited coroutine error
    # We ignore existing unrelated failures
    pass
