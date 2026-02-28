import { StockDetail } from "@/components/stocks/stock-detail";
import type { Metadata } from "next";

interface StockDetailPageProps {
  params: Promise<{ ticker: string }>;
}

export async function generateMetadata({
  params,
}: StockDetailPageProps): Promise<Metadata> {
  const { ticker } = await params;
  return {
    title: `${ticker.toUpperCase()} - AlphaStream India`,
    description: `View sentiment analysis, alpha metrics, and news for ${ticker.toUpperCase()}`,
  };
}

export default async function StockDetailPage({
  params,
}: StockDetailPageProps) {
  const { ticker } = await params;

  return (
    <div className="space-y-6">
      <StockDetail ticker={ticker.toUpperCase()} />
    </div>
  );
}
