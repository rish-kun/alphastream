import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const replaceMock = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: replaceMock,
    back: vi.fn(),
    prefetch: vi.fn(),
  }),
  useSearchParams: () => new URLSearchParams("topic=banking"),
}));

vi.mock("@/lib/api", () => ({
  getResearchStatus: vi.fn().mockResolvedValue({
    task_id: "task-1",
    status: "SUCCESS",
    progress: null,
    result: { status: "completed", new_articles: 2 },
    error: null,
  }),
}));

import { ResearchStatusPageClient } from "@/components/research/research-status-page-client";

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

describe("ResearchStatusPage", () => {
  beforeEach(() => {
    replaceMock.mockClear();
  });

  it("redirects to results page when task succeeds", async () => {
    renderWithProviders(
      <ResearchStatusPageClient taskId="task-1" />
    );

    expect(await screen.findByText("Deep Research Status")).toBeInTheDocument();

    await waitFor(() =>
      expect(replaceMock).toHaveBeenCalledWith(
        "/news/research/task-1/results?topic=banking"
      )
    );
  });
});
