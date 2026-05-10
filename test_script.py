from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func, and_, case
from app.models.sentiment import SentimentAnalysis
from sqlalchemy.dialects import postgresql

now = datetime.now(timezone.utc)
since = now - timedelta(hours=24)

stmt = select(
    func.avg(SentimentAnalysis.sentiment_score).label("market_sentiment"),
    func.count(case((SentimentAnalysis.sentiment_score > 0.3, 1))).label("bullish_count"),
    func.count(case((SentimentAnalysis.sentiment_score < -0.3, 1))).label("bearish_count"),
    func.count(case((
        and_(
            SentimentAnalysis.sentiment_score >= -0.3,
            SentimentAnalysis.sentiment_score <= 0.3
        ), 1
    ))).label("neutral_count")
).select_from(SentimentAnalysis).where(SentimentAnalysis.analyzed_at >= since)

print(stmt.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))
