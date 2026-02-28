import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { SentimentBadge } from "@/components/news/sentiment-badge";

describe("SentimentBadge", () => {
  it('renders "Bullish" for a positive score (0.3)', () => {
    render(<SentimentBadge score={0.3} />);

    expect(screen.getByText("Bullish")).toBeInTheDocument();
    expect(screen.getByText("(+0.30)")).toBeInTheDocument();
  });

  it('renders "Bearish" for a negative score (-0.35)', () => {
    render(<SentimentBadge score={-0.35} />);

    expect(screen.getByText("Bearish")).toBeInTheDocument();
    expect(screen.getByText("(-0.35)")).toBeInTheDocument();
  });

  it('renders "Neutral" for a near-zero score (0.0)', () => {
    render(<SentimentBadge score={0.0} />);

    expect(screen.getByText("Neutral")).toBeInTheDocument();
    expect(screen.getByText("(0.00)")).toBeInTheDocument();
  });

  it('renders "Very Bullish" for a high positive score (0.8)', () => {
    render(<SentimentBadge score={0.8} />);

    expect(screen.getByText("Very Bullish")).toBeInTheDocument();
    expect(screen.getByText("(+0.80)")).toBeInTheDocument();
  });
});
