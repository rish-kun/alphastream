export interface Article {
  id: string
  title: string
  content: string
  source: string
  url: string
  published_at: string
  sentiment?: SentimentAnalysis
  llm_analysis?: LLMAnalysis
}

export interface SentimentAnalysis {
  sentiment: 'positive' | 'negative' | 'neutral'
  confidence: number
  scores: {
    positive: number
    neutral: number
    negative: number
  }
}

export interface LLMAnalysis {
  summary: string
  key_points: string[]
  market_impact: string
  affected_sectors: string[]
  trading_signals: string[]
}

export interface MarketSummary {
  summary: string
  key_trends: string[]
  notable_movements: string[]
}
