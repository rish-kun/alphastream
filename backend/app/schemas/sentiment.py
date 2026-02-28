from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class SentimentResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    article_id: uuid.UUID
    sentiment_score: float
    confidence: float
    explanation: str | None = None
    impact_timeline: str
    finbert_score: float | None = None
    llm_score: float | None = None
    llm_provider: str | None = None
    analyzed_at: datetime


class AlphaMetricResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    stock_id: uuid.UUID | None = None
    sector: str | None = None
    expectation_gap: float
    narrative_velocity: float
    sentiment_divergence: float
    composite_score: float
    signal: str
    conviction: float
    computed_at: datetime
    window_hours: int


class SentimentOverview(BaseModel):
    market_sentiment: float
    bullish_count: int
    bearish_count: int
    neutral_count: int
    top_movers: list[AlphaMetricResponse]


class SectorSentiment(BaseModel):
    sector: str
    sentiment_score: float
    article_count: int
    top_stocks: list[str]
