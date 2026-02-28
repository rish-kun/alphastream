import type { SignalType } from "./stock";

export interface AlphaMetric {
  id: string;
  stock_id: string | null;
  ticker: string | null;
  company_name: string | null;
  sector: string | null;
  expectation_gap: number;
  narrative_velocity: number;
  sentiment_divergence: number;
  composite_score: number;
  signal: SignalType;
  conviction: number;
  computed_at: string;
}

export interface SentimentOverview {
  market_sentiment: number;
  bullish_count: number;
  bearish_count: number;
  neutral_count: number;
  total_articles: number;
  sentiment_trend: SentimentTrendPoint[];
  sectors: SectorSentiment[];
  updated_at: string;
}

export interface SentimentTrendPoint {
  timestamp: string;
  sentiment: number;
  volume: number;
}

export interface SectorSentiment {
  sector: string;
  sentiment_score: number;
  news_count: number;
  top_signal: SignalType;
  change_24h: number;
}

export interface SentimentAnalysis {
  article_id: string;
  sentiment_score: number;
  confidence: number;
  explanation: string | null;
  impact_timeline: string;
  entities: string[];
  topics: string[];
}

export interface CompositeSignal {
  ticker: string;
  company_name: string;
  signal: SignalType;
  composite_score: number;
  conviction: number;
  components: {
    expectation_gap: number;
    narrative_velocity: number;
    sentiment_divergence: number;
  };
  reasoning: string | null;
  computed_at: string;
}
