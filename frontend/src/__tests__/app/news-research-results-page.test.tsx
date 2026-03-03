import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

vi.mock("next/navigation", () => ({
  useSearchParams: () => new URLSearchParams("topic=inflation"),
}));

vi.mock("@/lib/api", () => ({
  getResearchStatus: vi.fn().mockResolvedValue({
    task_id: "task-10",
    status: "SUCCESS",
    progress: null,
    result: { status: "completed" },
    error: null,
  }),
  getResearchResult: vi.fn().mockResolvedValue({
    task_id: "task-10",
    status: "SUCCESS",
    topic: "inflation",
    ticker: null,
    new_articles: 3,
    total_found: 9,
    query_count: 3,
    started_at: null,
    completed_at: null,
    duration_seconds: null,
    sentiment: {
      overall_score: 0.31,
      overall_label: "bullish",
      analyzed_articles: 2,
      pending_articles: 0,
      bullish_count: 2,
      neutral_count: 0,
      bearish_count: 0,
    },
    articles: [
      {
        id: "a1",
        title: "Inflation cools in Q4",
        summary: "Summary",
        url: "https://example.com/a1",
        source: "Deep Research",
        published_at: "2026-03-03T10:00:00Z",
        category: "deep_research",
        mentions: [],
        sentiment_analyses: [{ sentiment_score: 0.4, confidence: 0.8 }],
      },
    ],
  }),
}));

import { ResearchResultsPageClient } from "@/components/research/research-results-page-client";

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
  );
}

describe("ResearchResultsPage", () => {
  it("renders sentiment summary and researched articles", async () => {
    renderWithProviders(
      <ResearchResultsPageClient taskId="task-10" />
    );

    expect(await screen.findByText("Overall Sentiment")).toBeInTheDocument();
    expect(screen.getByText("Deep Research Results")).toBeInTheDocument();
    expect(screen.getByText("Coverage")).toBeInTheDocument();
    expect(screen.getByText("Inflation cools in Q4")).toBeInTheDocument();
  });
});
