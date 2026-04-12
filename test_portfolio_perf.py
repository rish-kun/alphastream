import asyncio
from app.database import async_session_factory
from app.services.portfolio_service import PortfolioService
import uuid

async def main():
    async with async_session_factory() as db:
        service = PortfolioService(db)
        # Just compiling the query to see
