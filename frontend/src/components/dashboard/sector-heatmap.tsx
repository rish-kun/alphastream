"use client";

import { useQuery } from "@tanstack/react-query";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { Grid3x3, TrendingUp, TrendingDown, Minus } from "lucide-react";
import { getSectorSentiment } from "@/lib/api";
import type { SectorSentiment } from "@/types/sentiment";
import type { SignalType } from "@/types/stock";

// Fallback data
const fallbackSectors: SectorSentiment[] = [
  { sector: "Financial Services", sentiment_score: 0.45, news_count: 28, top_signal: "buy" as SignalType, change_24h: 0.08 },
  { sector: "Technology", sentiment_score: -0.22, news_count: 19, top_signal: "hold" as SignalType, change_24h: -0.15 },
  { sector: "Energy", sentiment_score: 0.61, news_count: 15, top_signal: "strong_buy" as SignalType, change_24h: 0.12 },
  { sector: "FMCG", sentiment_score: 0.12, news_count: 11, top_signal: "hold" as SignalType, change_24h: 0.03 },
  { sector: "Healthcare", sentiment_score: 0.33, news_count: 9, top_signal: "buy" as SignalType, change_24h: 0.05 },
  { sector: "Telecom", sentiment_score: -0.08, news_count: 7, top_signal: "hold" as SignalType, change_24h: -0.02 },
  { sector: "Automobiles", sentiment_score: 0.28, news_count: 12, top_signal: "buy" as SignalType, change_24h: 0.10 },
  { sector: "Metals & Mining", sentiment_score: -0.35, news_count: 8, top_signal: "sell" as SignalType, change_24h: -0.18 },
];

function getSentimentColor(score: number): string {
  if (score > 0.3) return "text-green-600 dark:text-green-400";
  if (score > 0.1) return "text-green-500 dark:text-green-500";
  if (score < -0.3) return "text-red-600 dark:text-red-400";
  if (score < -0.1) return "text-red-500 dark:text-red-500";
  return "text-yellow-600 dark:text-yellow-400";
}

function getSentimentBgIntensity(score: number): string {
  const abs = Math.abs(score);
  if (score > 0) {
    if (abs > 0.5) return "bg-green-500/15 border-green-500/30";
    if (abs > 0.3) return "bg-green-500/10 border-green-500/20";
    return "bg-green-500/5 border-green-500/10";
  }
  if (score < 0) {
    if (abs > 0.5) return "bg-red-500/15 border-red-500/30";
    if (abs > 0.3) return "bg-red-500/10 border-red-500/20";
    return "bg-red-500/5 border-red-500/10";
  }
  return "bg-yellow-500/5 border-yellow-500/10";
}

function getSignalBadgeVariant(
  signal: SignalType
): "default" | "secondary" | "destructive" | "outline" {
  if (signal === "strong_buy" || signal === "buy") return "default";
  if (signal === "strong_sell" || signal === "sell") return "destructive";
  return "secondary";
}

function getSignalLabel(signal: SignalType): string {
  const labels: Record<SignalType, string> = {
    strong_buy: "Strong Buy",
    buy: "Buy",
    hold: "Hold",
    sell: "Sell",
    strong_sell: "Strong Sell",
  };
  return labels[signal] ?? signal;
}

function ChangeIndicator({ change }: { change: number }) {
  if (change > 0.01) {
    return (
      <span className="flex items-center gap-0.5 text-xs text-green-600 dark:text-green-400">
        <TrendingUp className="h-3 w-3" />+{(change * 100).toFixed(0)}%
      </span>
    );
  }
  if (change < -0.01) {
    return (
      <span className="flex items-center gap-0.5 text-xs text-red-600 dark:text-red-400">
        <TrendingDown className="h-3 w-3" />
        {(change * 100).toFixed(0)}%
      </span>
    );
  }
  return (
    <span className="flex items-center gap-0.5 text-xs text-muted-foreground">
      <Minus className="h-3 w-3" />0%
    </span>
  );
}

export function SectorHeatmap() {
  const { data: sectors, isLoading } = useQuery({
    queryKey: ["sector-sentiment"],
    queryFn: getSectorSentiment,
    refetchInterval: 120000,
  });

  const sectorData = sectors ?? fallbackSectors;

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Sector Sentiment</CardTitle>
          <CardDescription>Loading sector data...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 sm:grid-cols-2">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-24 w-full rounded-lg" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Grid3x3 className="h-5 w-5" />
          Sector Sentiment
        </CardTitle>
        <CardDescription>
          Sentiment heatmap by market sector — color intensity reflects strength
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid gap-3 sm:grid-cols-2">
          {sectorData.map((sector) => (
            <div
              key={sector.sector}
              className={`rounded-lg border p-3 transition-colors ${getSentimentBgIntensity(sector.sentiment_score)}`}
            >
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <p className="text-sm font-semibold leading-none">
                    {sector.sector}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {sector.news_count} articles
                  </p>
                </div>
                <div className="flex flex-col items-end gap-1">
                  <span
                    className={`text-lg font-bold tabular-nums ${getSentimentColor(sector.sentiment_score)}`}
                  >
                    {sector.sentiment_score > 0 ? "+" : ""}
                    {sector.sentiment_score.toFixed(2)}
                  </span>
                  <ChangeIndicator change={sector.change_24h} />
                </div>
              </div>
              <div className="mt-2 flex items-center justify-between">
                <Progress
                  value={((sector.sentiment_score + 1) / 2) * 100}
                  className="h-1.5 flex-1 mr-2"
                />
                <Badge
                  variant={getSignalBadgeVariant(sector.top_signal)}
                  className="shrink-0 text-[10px] px-1.5 py-0"
                >
                  {getSignalLabel(sector.top_signal)}
                </Badge>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
