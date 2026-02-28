from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SentimentAnalysis(Base):
    __tablename__ = "sentiment_analyses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    article_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("news_articles.id", ondelete="CASCADE"),
        nullable=False,
    )
    sentiment_score: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    impact_timeline: Mapped[str] = mapped_column(String(20), nullable=False)
    finbert_score: Mapped[float | None] = mapped_column(Numeric(4, 3), nullable=True)
    llm_score: Mapped[float | None] = mapped_column(Numeric(4, 3), nullable=True)
    llm_provider: Mapped[str | None] = mapped_column(String(20), nullable=True)
    raw_response: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class AlphaMetric(Base):
    __tablename__ = "alpha_metrics"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    stock_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("stocks.id", ondelete="CASCADE"),
        nullable=True,
    )
    sector: Mapped[str | None] = mapped_column(String(100), nullable=True)
    expectation_gap: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)
    narrative_velocity: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)
    sentiment_divergence: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)
    composite_score: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)
    signal: Mapped[str] = mapped_column(String(20), nullable=False)
    conviction: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    window_hours: Mapped[int] = mapped_column(Integer, nullable=False)


class SocialSentiment(Base):
    __tablename__ = "social_sentiments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    article_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("news_articles.id", ondelete="CASCADE"),
        nullable=True,
    )
    stock_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("stocks.id", ondelete="CASCADE"),
        nullable=True,
    )
    platform: Mapped[str] = mapped_column(String(20), nullable=False)
    post_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sentiment_score: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False)
    engagement: Mapped[int] = mapped_column(
        Integer, default=0, server_default=text("0")
    )
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
