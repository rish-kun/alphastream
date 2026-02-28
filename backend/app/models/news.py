from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class NewsArticle(Base):
    __tablename__ = "news_articles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    full_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    source: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Relationships
    mentions: Mapped[list["ArticleStockMention"]] = relationship(
        "ArticleStockMention", back_populates="article", lazy="selectin"
    )
    sentiment_analyses: Mapped[list["SentimentAnalysis"]] = relationship(
        "SentimentAnalysis", backref="article", lazy="selectin"
    )


class ArticleStockMention(Base):
    __tablename__ = "article_stock_mentions"

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
    stock_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("stocks.id", ondelete="CASCADE"),
        nullable=False,
    )
    relevance_score: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False)
    mentioned_as: Mapped[str] = mapped_column(String(100), nullable=False)
    impact_direction: Mapped[str] = mapped_column(String(10), nullable=False)

    # Relationships
    article: Mapped["NewsArticle"] = relationship(
        "NewsArticle", back_populates="mentions", lazy="selectin"
    )
    stock: Mapped["Stock"] = relationship(
        "Stock", back_populates="mentions", lazy="selectin"
    )
