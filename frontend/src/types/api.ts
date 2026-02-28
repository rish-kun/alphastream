export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface ApiError {
  detail: string;
  status_code: number;
}

export interface TokenResponse {
  access_token: string;
  refresh_token?: string;
  token_type: string;
  user: UserProfile;
}

export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
}

export interface Portfolio {
  id: string;
  name: string;
  description: string | null;
  user_id: string;
  stocks: PortfolioStock[];
  created_at: string;
  updated_at: string;
}

export interface PortfolioStock {
  stock_id: string;
  ticker: string;
  company_name: string;
  weight: number;
  added_at: string;
}

export interface CreatePortfolioRequest {
  name: string;
  description?: string;
  stock_ids?: string[];
}

export interface PortfoliosResponse {
  portfolios: Portfolio[];
}

export interface PortfolioNewsResponse {
  items: PortfolioNewsItem[];
  total: number;
}

export interface PortfolioNewsItem {
  id: string;
  title: string;
  source: string;
  published_at: string;
  sentiment_score: number | null;
  ticker: string;
}

export interface PortfolioAlphaResponse {
  metrics: PortfolioAlphaMetric[];
}

export interface PortfolioAlphaMetric {
  ticker: string;
  company_name: string;
  composite_score: number;
  signal: string;
  conviction: number;
}

// ─── Extensive Research ──────────────────────────────────────────────────────

export interface ResearchTaskResponse {
  task_id: string;
  status: string;
  message: string;
}

export interface TopicResearchRequest {
  topic: string;
}

export interface TaskStatusResponse {
  task_id: string;
  status: string;
  progress: Record<string, unknown> | null;
  result: Record<string, unknown> | null;
  error: string | null;
}
