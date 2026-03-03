import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const pushMock = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: pushMock,
    replace: vi.fn(),
    back: vi.fn(),
    prefetch: vi.fn(),
  }),
}));

vi.mock("@/lib/api", () => ({
  researchTopic: vi.fn().mockResolvedValue({
    task_id: "task-topic-1",
    status: "dispatched",
    message: "ok",
  }),
}));

import { TopicResearchButton } from "@/components/research/topic-research-button";

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

describe("TopicResearchButton", () => {
  it("routes to the dedicated research status page after dispatch", async () => {
    const user = userEvent.setup();
    renderWithProviders(<TopicResearchButton topic="steel demand" />);

    await user.click(screen.getByRole("button", { name: /deep research/i }));

    expect(pushMock).toHaveBeenCalledWith(
      "/news/research/task-topic-1?topic=steel+demand"
    );
  });
});
