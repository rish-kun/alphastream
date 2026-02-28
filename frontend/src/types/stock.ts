export interface Stock {
  id: string;
  ticker: string;
  exchange: string;
  company_name: string;
  sector: string;
  industry: string;
  market_cap: number | null;
  last_price: number | null;
  price_updated_at: string | null;
}

export interface StockSearchResult {
  stocks: Stock[];
  total: number;
}

export interface StockAlphaMetric {
  stock_id: string;
  ticker: string;
  company_name: string;
  composite_score: number;
  signal: SignalType;
  conviction: number;
  expectation_gap: number;
  narrative_velocity: number;
  sentiment_divergence: number;
  computed_at: string;
}

export interface StockNews {
  id: string;
  title: string;
  source: string;
  published_at: string;
  sentiment_score: number;
  confidence: number;
  impact_timeline: string;
}

export type SignalType =
  | "strong_buy"
  | "buy"
  | "hold"
  | "sell"
  | "strong_sell";

export interface Sector {
  name: string;
  stock_count: number;
}

export interface SectorsResponse {
  sectors: Sector[];
}

export interface StockNewsResponse {
  items: StockNews[];
  total: number;
  page: number;
  size: number;
}

export interface AlphaMetricEntry {
  expectation_gap: number;
  narrative_velocity: number;
  sentiment_divergence: number;
  composite_score: number;
  signal: SignalType;
  conviction: number;
  computed_at: string;
  window_hours: number;
}

export interface StockAlphaResponse {
  metrics: AlphaMetricEntry[];
}
