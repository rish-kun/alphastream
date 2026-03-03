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
import { Grid3x3 } from "lucide-react";
import { getSectorSentiment } from "@/lib/api";
import type { SectorSentiment } from "@/lib/api";


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

export function SectorHeatmap() {
  const { data: sectors, isLoading, isError } = useQuery({
    queryKey: ["sector-sentiment"],
    queryFn: getSectorSentiment,
    refetchInterval: 120000,
  });

  const sectorData = sectors ?? [];

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

  if (isError || sectorData.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Grid3x3 className="h-5 w-5" />
            Sector Sentiment
          </CardTitle>
          <CardDescription>
            Sentiment heatmap by market sector
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 text-center text-muted-foreground">
            <Grid3x3 className="mb-2 h-8 w-8 opacity-50" />
            <p className="text-sm">No sector sentiment data available</p>
            <p className="text-xs">Data will appear once news articles are analyzed</p>
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
              className={`rounded-lg border p-3 transition-colors ${getSentimentBgIntensity(sector.avg_sentiment)}`}
            >
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <p className="text-sm font-semibold leading-none">
                    {sector.sector}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {sector.article_count} articles
                  </p>
                </div>
                <div className="flex flex-col items-end gap-1">
                  <span
                    className={`text-lg font-bold tabular-nums ${getSentimentColor(sector.avg_sentiment)}`}
                  >
                    {sector.avg_sentiment > 0 ? "+" : ""}
                    {sector.avg_sentiment.toFixed(2)}
                  </span>
                </div>
              </div>
              <div className="mt-2 flex items-center justify-between">
                <Progress
                  value={((sector.avg_sentiment + 1) / 2) * 100}
                  className="h-1.5 flex-1 mr-2"
                />
                <div className="flex gap-1">
                  {sector.top_tickers.slice(0, 2).map((ticker) => (
                    <Badge
                      key={ticker}
                      variant="secondary"
                      className="shrink-0 text-[10px] px-1.5 py-0"
                    >
                      {ticker}
                    </Badge>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
