import asyncio
from app.database import async_session_factory
from app.services.news_service import NewsService
from app.schemas.news import NewsFeedQuery

async def main():
    async with async_session_factory() as db:
        service = NewsService(db)
        query = NewsFeedQuery(page=1, page_size=10, ticker="AAPL")
        try:
            result = await service.get_news_feed(query)
            print("Total:", result.total)
            print("Articles:", len(result.articles))
        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":
    asyncio.run(main())
