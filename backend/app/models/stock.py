from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Numeric, String, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Stock(Base):
    __tablename__ = "stocks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    ticker: Mapped[str] = mapped_column(
        String(20), unique=True, index=True, nullable=False
    )
    exchange: Mapped[str] = mapped_column(String(10), nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sector: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    industry: Mapped[str] = mapped_column(String(100), nullable=False)
    market_cap: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    aliases: Mapped[list] = mapped_column(
        JSONB, server_default=text("'[]'::jsonb"), nullable=False
    )
    last_price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    price_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    mentions: Mapped[list["ArticleStockMention"]] = relationship(
        "ArticleStockMention", back_populates="stock", lazy="selectin"
    )
    alpha_metrics: Mapped[list["AlphaMetric"]] = relationship(
        "AlphaMetric", backref="stock", lazy="selectin"
    )
    portfolio_stocks: Mapped[list["PortfolioStock"]] = relationship(
        "PortfolioStock", back_populates="stock", lazy="selectin"
    )
