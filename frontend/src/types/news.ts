import type { Stock } from "./stock";

// --- API response types (match backend exactly) ---

export interface NewsMention {
  ticker: string;
  company_name: string;
  relevance_score: number;
}

export interface SentimentAnalysisEntry {
  sentiment_score: number;
  confidence: number;
  model?: string;
  explanation?: string | null;
  impact_timeline?: string;
}

/** Item returned by GET /api/v1/news/ */
export interface NewsArticleListItem {
  id: string;
  title: string;
  summary: string | null;
  url: string;
  source: string;
  published_at: string;
  category: string | null;
  mentions: NewsMention[];
  sentiment_analyses: SentimentAnalysisEntry[];
}

/** Paginated response from GET /api/v1/news/ */
export interface NewsFeedResponse {
  items: NewsArticleListItem[];
  total: number;
  page: number;
  size: number;
}

/** Params for news feed query */
export interface NewsFeedParams {
  page?: number;
  size?: number;
  source?: string;
  ticker?: string;
  start_date?: string;
  end_date?: string;
}

/** Trending article from GET /api/v1/news/trending */
export interface TrendingArticle {
  id: string;
  title: string;
  source: string;
  published_at: string;
  sentiment_score: number | null;
  mentions: NewsMention[];
}

/** Response from GET /api/v1/news/trending */
export interface TrendingNewsResponse {
  articles: TrendingArticle[];
}

/** Full article from GET /api/v1/news/{id} */
export interface NewsArticleDetail {
  id: string;
  title: string;
  summary: string | null;
  full_text: string | null;
  url: string;
  source: string;
  published_at: string;
  category: string | null;
  mentions: NewsMention[];
  sentiment_analyses: SentimentAnalysisEntry[];
}

// --- Legacy types (kept for backward compatibility) ---

export interface NewsArticle {
  id: string;
  title: string;
  summary: string | null;
  url: string;
  source: string;
  published_at: string;
  category: string | null;
  sentiment?: ArticleSentiment;
  mentioned_stocks?: Stock[];
}

export interface ArticleSentiment {
  sentiment_score: number;
  confidence: number;
  explanation: string | null;
  impact_timeline: string;
}

export interface NewsFeedItem {
  id: string;
  title: string;
  source: string;
  published_at: string;
  category: string | null;
  sentiment_score: number | null;
  sentiment_label: "bullish" | "bearish" | "neutral";
  confidence: number | null;
  tickers: string[];
}

export interface TrendingNews {
  articles: NewsArticle[];
  trending_topics: string[];
  updated_at: string;
}
