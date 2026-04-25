import asyncio
from sqlalchemy import select, func
from app.models.news import NewsArticle, ArticleStockMention
from app.models.stock import Stock

async def main():
    ticker = "AAPL"
    stmt = (
        select(NewsArticle)
        .where(
            NewsArticle.mentions.any(
                ArticleStockMention.stock.has(
                    func.lower(Stock.ticker) == func.lower(ticker)
                )
            )
        )
    )
    print(stmt)

if __name__ == "__main__":
    asyncio.run(main())
