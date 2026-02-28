import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ResearchToggle } from "@/components/research/research-toggle";

// Mock the API module
vi.mock("@/lib/api", () => ({
  researchStock: vi.fn().mockResolvedValue({
    task_id: "task-1",
    status: "PENDING",
    message: "Research started",
  }),
  researchPortfolio: vi.fn(),
  researchTopic: vi.fn(),
  getResearchStatus: vi.fn(),
}));

import { researchStock } from "@/lib/api";

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

describe("ResearchToggle", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the "Extensive Research" label and button in default mode', () => {
    renderWithProviders(
      <ResearchToggle type="stock" ticker="RELIANCE" />
    );

    expect(screen.getByText("Extensive Research")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /start research/i })
    ).toBeInTheDocument();
  });

  it("clicking the button triggers the research mutation", async () => {
    const user = userEvent.setup();

    renderWithProviders(
      <ResearchToggle type="stock" ticker="RELIANCE" />
    );

    const button = screen.getByRole("button", { name: /start research/i });
    await user.click(button);

    expect(researchStock).toHaveBeenCalledWith("RELIANCE");
  });

  it("renders differently in compact mode", () => {
    renderWithProviders(
      <ResearchToggle type="stock" ticker="TCS" compact />
    );

    // Compact mode should NOT show the "Extensive Research" label
    expect(screen.queryByText("Extensive Research")).not.toBeInTheDocument();
    // Should show "Deep Research" button text
    expect(
      screen.getByRole("button", { name: /deep research/i })
    ).toBeInTheDocument();
  });

  it("shows loading state after clicking", async () => {
    // Make the mutation stay pending
    vi.mocked(researchStock).mockReturnValue(new Promise(() => {}));

    const user = userEvent.setup();

    renderWithProviders(
      <ResearchToggle type="stock" ticker="INFY" />
    );

    const button = screen.getByRole("button", { name: /start research/i });
    await user.click(button);

    // Button should now show "Researching..." text
    expect(screen.getByText("Researching...")).toBeInTheDocument();
    // Button should be disabled
    expect(
      screen.getByRole("button", { name: /researching/i })
    ).toBeDisabled();
  });
});
