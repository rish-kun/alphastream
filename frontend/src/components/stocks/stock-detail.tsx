"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  TrendingUp,
  TrendingDown,
  ArrowLeft,
  ExternalLink,
  Clock,
  Building2,
  BarChart3,
  Newspaper,
  Activity,
  AlertCircle,
} from "lucide-react";
import Link from "next/link";
import { formatDistanceToNow, format } from "date-fns";
import { getStock, getStockNews, getStockAlpha } from "@/lib/api";
import { useWebSocketSubscription } from "@/hooks/use-websocket";
import { ResearchToggle } from "@/components/research/research-toggle";
import type { SignalType, AlphaMetricEntry } from "@/types/stock";

interface StockDetailProps {
  ticker: string;
}

const SIGNAL_CONFIG: Record<
  string,
  { label: string; color: string; bgColor: string }
> = {
  strong_buy: {
    label: "Strong Buy",
    color: "text-green-700 dark:text-green-400",
    bgColor: "bg-green-100 dark:bg-green-900/30 border-green-200 dark:border-green-800",
  },
  buy: {
    label: "Buy",
    color: "text-green-600 dark:text-green-400",
    bgColor: "bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800",
  },
  hold: {
    label: "Hold",
    color: "text-gray-600 dark:text-gray-400",
    bgColor: "bg-gray-100 dark:bg-gray-800/30 border-gray-200 dark:border-gray-700",
  },
  sell: {
    label: "Sell",
    color: "text-red-600 dark:text-red-400",
    bgColor: "bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800",
  },
  strong_sell: {
    label: "Strong Sell",
    color: "text-red-700 dark:text-red-400",
    bgColor: "bg-red-100 dark:bg-red-900/30 border-red-200 dark:border-red-800",
  },
};

function getSignalConfig(signal: string) {
  return (
    SIGNAL_CONFIG[signal] ?? {
      label: signal,
      color: "text-gray-600",
      bgColor: "bg-gray-100 border-gray-200",
    }
  );
}

function formatMarketCap(value: number | null): string {
  if (value == null) return "N/A";
  if (value >= 1e12) return `₹${(value / 1e12).toFixed(2)}T`;
  if (value >= 1e9) return `₹${(value / 1e9).toFixed(2)}B`;
  if (value >= 1e7) return `₹${(value / 1e7).toFixed(2)}Cr`;
  if (value >= 1e5) return `₹${(value / 1e5).toFixed(2)}L`;
  return `₹${value.toLocaleString("en-IN")}`;
}

function MetricBar({
  label,
  value,
  min = -1,
  max = 1,
}: {
  label: string;
  value: number;
  min?: number;
  max?: number;
}) {
  const range = max - min;
  const normalized = Math.max(0, Math.min(100, ((value - min) / range) * 100));
  const isPositive = value > 0;

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium">{label}</span>
        <span
          className={`text-sm font-semibold tabular-nums ${
            isPositive
              ? "text-green-600 dark:text-green-400"
              : value < 0
                ? "text-red-600 dark:text-red-400"
                : "text-muted-foreground"
          }`}
        >
          {value > 0 ? "+" : ""}
          {value.toFixed(3)}
        </span>
      </div>
      <div className="relative h-2 w-full overflow-hidden rounded-full bg-muted">
        <div
          className={`h-full rounded-full transition-all ${
            isPositive ? "bg-green-500" : value < 0 ? "bg-red-500" : "bg-gray-400"
          }`}
          style={{ width: `${normalized}%` }}
        />
      </div>
    </div>
  );
}

export function StockDetail({ ticker }: StockDetailProps) {
  const [newsPage, setNewsPage] = useState(1);
  const queryClient = useQueryClient();

  // Fetch stock data
  const {
    data: stock,
    isLoading: isStockLoading,
    error: stockError,
  } = useQuery({
    queryKey: ["stock", ticker],
    queryFn: () => getStock(ticker),
  });

  // Fetch stock news
  const {
    data: newsData,
    isLoading: isNewsLoading,
  } = useQuery({
    queryKey: ["stock", ticker, "news", newsPage],
    queryFn: () => getStockNews(ticker, newsPage, 10),
  });

  // Fetch alpha metrics
  const {
    data: alphaData,
    isLoading: isAlphaLoading,
  } = useQuery({
    queryKey: ["stock", ticker, "alpha"],
    queryFn: () => getStockAlpha(ticker),
  });

  // WebSocket subscription for real-time updates
  useWebSocketSubscription(`stock:${ticker}`, "stock_update", (data) => {
    queryClient.invalidateQueries({ queryKey: ["stock", ticker] });
  });

  useWebSocketSubscription(`stock:${ticker}`, "alpha_update", (data) => {
    queryClient.invalidateQueries({ queryKey: ["stock", ticker, "alpha"] });
  });

  const latestAlpha: AlphaMetricEntry | null =
    alphaData?.metrics?.[0] ?? null;
  const signalConfig = latestAlpha
    ? getSignalConfig(latestAlpha.signal)
    : null;

  if (stockError) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" asChild>
            <Link href="/stocks">
              <ArrowLeft className="h-4 w-4" />
            </Link>
          </Button>
          <h1 className="text-3xl font-bold tracking-tight">{ticker}</h1>
        </div>
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Failed to load stock data for {ticker}.{" "}
            {stockError instanceof Error ? stockError.message : "Unknown error"}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start gap-4">
        <Button variant="ghost" size="icon" asChild className="mt-1">
          <Link href="/stocks">
            <ArrowLeft className="h-4 w-4" />
          </Link>
        </Button>
        <div className="flex-1">
          <div className="flex flex-wrap items-center gap-3">
            {isStockLoading ? (
              <>
                <Skeleton className="h-9 w-40" />
                <Skeleton className="h-6 w-24 rounded-full" />
              </>
            ) : (
              <>
                <h1 className="text-3xl font-bold tracking-tight">
                  {stock?.ticker}
                </h1>
                {signalConfig && (
                  <Badge
                    className={`${signalConfig.bgColor} ${signalConfig.color} border gap-1`}
                  >
                    {latestAlpha!.signal.includes("buy") ? (
                      <TrendingUp className="h-3 w-3" />
                    ) : latestAlpha!.signal.includes("sell") ? (
                      <TrendingDown className="h-3 w-3" />
                    ) : null}
                    {signalConfig.label}
                  </Badge>
                )}
              </>
            )}
          </div>
          {isStockLoading ? (
            <div className="mt-1 space-y-1">
              <Skeleton className="h-4 w-60" />
              <Skeleton className="h-3 w-40" />
            </div>
          ) : (
            <>
              <p className="text-muted-foreground">{stock?.company_name}</p>
              <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground mt-1">
                <Building2 className="h-3.5 w-3.5" />
                <span>{stock?.sector}</span>
                <span className="text-muted-foreground/40">|</span>
                <span>{stock?.industry}</span>
                {stock?.exchange && (
                  <>
                    <span className="text-muted-foreground/40">|</span>
                    <span>{stock.exchange}</span>
                  </>
                )}
              </div>
            </>
          )}
        </div>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center gap-1.5">
              <span>Last Price</span>
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isStockLoading ? (
              <Skeleton className="h-8 w-28" />
            ) : stock?.last_price != null ? (
              <div>
                <p className="text-2xl font-bold tabular-nums">
                  ₹
                  {stock.last_price.toLocaleString("en-IN", {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })}
                </p>
                {stock.price_updated_at && (
                  <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {formatDistanceToNow(new Date(stock.price_updated_at), {
                      addSuffix: true,
                    })}
                  </p>
                )}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">N/A</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Market Cap</CardDescription>
          </CardHeader>
          <CardContent>
            {isStockLoading ? (
              <Skeleton className="h-8 w-24" />
            ) : (
              <p className="text-2xl font-bold">
                {formatMarketCap(stock?.market_cap ?? null)}
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Composite Score</CardDescription>
          </CardHeader>
          <CardContent>
            {isAlphaLoading ? (
              <Skeleton className="h-8 w-20" />
            ) : latestAlpha ? (
              <p
                className={`text-2xl font-bold tabular-nums ${
                  latestAlpha.composite_score > 0
                    ? "text-green-600 dark:text-green-400"
                    : latestAlpha.composite_score < 0
                      ? "text-red-600 dark:text-red-400"
                      : ""
                }`}
              >
                {latestAlpha.composite_score > 0 ? "+" : ""}
                {latestAlpha.composite_score.toFixed(3)}
              </p>
            ) : (
              <p className="text-sm text-muted-foreground">No data</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Conviction</CardDescription>
          </CardHeader>
          <CardContent>
            {isAlphaLoading ? (
              <Skeleton className="h-8 w-20" />
            ) : latestAlpha ? (
              <div className="space-y-2">
                <p className="text-2xl font-bold tabular-nums">
                  {Math.round(latestAlpha.conviction)}%
                </p>
                <Progress value={latestAlpha.conviction} className="h-2" />
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No data</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Extensive Research */}
      <ResearchToggle type="stock" ticker={ticker} />

      {/* Tabs: News / Alpha Metrics */}
      <Tabs defaultValue="metrics">
        <TabsList>
          <TabsTrigger value="metrics" className="gap-1.5">
            <Activity className="h-3.5 w-3.5" />
            Alpha Metrics
          </TabsTrigger>
          <TabsTrigger value="news" className="gap-1.5">
            <Newspaper className="h-3.5 w-3.5" />
            News
          </TabsTrigger>
        </TabsList>

        <TabsContent value="metrics" className="mt-4">
          <div className="grid gap-4 lg:grid-cols-2">
            {/* Current Metrics */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Current Metrics</CardTitle>
                <CardDescription>
                  Latest alpha signal components for {ticker}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {isAlphaLoading ? (
                  <div className="space-y-4">
                    {Array.from({ length: 4 }).map((_, i) => (
                      <div key={i} className="space-y-2">
                        <div className="flex items-center justify-between">
                          <Skeleton className="h-4 w-32" />
                          <Skeleton className="h-4 w-16" />
                        </div>
                        <Skeleton className="h-2 w-full rounded-full" />
                      </div>
                    ))}
                  </div>
                ) : latestAlpha ? (
                  <div className="space-y-4">
                    <MetricBar
                      label="Expectation Gap"
                      value={latestAlpha.expectation_gap}
                    />
                    <MetricBar
                      label="Narrative Velocity"
                      value={latestAlpha.narrative_velocity}
                    />
                    <MetricBar
                      label="Sentiment Divergence"
                      value={latestAlpha.sentiment_divergence}
                    />
                    <Separator />
                    <MetricBar
                      label="Composite Score"
                      value={latestAlpha.composite_score}
                    />
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground text-center py-8">
                    No alpha metrics available for {ticker}
                  </p>
                )}
              </CardContent>
            </Card>

            {/* Signal Summary */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Signal Summary</CardTitle>
                <CardDescription>
                  Overall recommendation and conviction level
                </CardDescription>
              </CardHeader>
              <CardContent>
                {isAlphaLoading ? (
                  <div className="space-y-4">
                    <Skeleton className="h-20 w-full rounded-lg" />
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-3/4" />
                  </div>
                ) : latestAlpha && signalConfig ? (
                  <div className="space-y-6">
                    <div
                      className={`flex flex-col items-center justify-center rounded-lg border p-6 ${signalConfig.bgColor}`}
                    >
                      <p className="text-sm font-medium text-muted-foreground mb-1">
                        Signal
                      </p>
                      <p className={`text-2xl font-bold ${signalConfig.color}`}>
                        {signalConfig.label}
                      </p>
                    </div>

                    <div className="space-y-3">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Conviction</span>
                        <span className="font-semibold">
                          {Math.round(latestAlpha.conviction)}%
                        </span>
                      </div>
                      <Progress value={latestAlpha.conviction} className="h-3" />
                    </div>

                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Window</span>
                      <span className="font-medium">
                        {latestAlpha.window_hours}h
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Computed</span>
                      <span className="font-medium">
                        {formatDistanceToNow(
                          new Date(latestAlpha.computed_at),
                          { addSuffix: true }
                        )}
                      </span>
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground text-center py-8">
                    No signal data available
                  </p>
                )}
              </CardContent>
            </Card>

            {/* Historical Metrics */}
            {alphaData && alphaData.metrics.length > 1 && (
              <Card className="lg:col-span-2">
                <CardHeader>
                  <CardTitle className="text-base">Metrics History</CardTitle>
                  <CardDescription>
                    Recent alpha metric computations
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="grid grid-cols-6 gap-2 text-xs font-medium text-muted-foreground border-b pb-2">
                      <span>Time</span>
                      <span className="text-right">Exp. Gap</span>
                      <span className="text-right">Velocity</span>
                      <span className="text-right">Divergence</span>
                      <span className="text-right">Composite</span>
                      <span className="text-right">Signal</span>
                    </div>
                    {alphaData.metrics.slice(0, 10).map((m, i) => {
                      const sc = getSignalConfig(m.signal);
                      return (
                        <div
                          key={i}
                          className="grid grid-cols-6 gap-2 text-xs py-1.5 border-b border-muted/50 last:border-0"
                        >
                          <span className="text-muted-foreground">
                            {formatDistanceToNow(new Date(m.computed_at), {
                              addSuffix: true,
                            })}
                          </span>
                          <span
                            className={`text-right tabular-nums ${
                              m.expectation_gap > 0
                                ? "text-green-600"
                                : m.expectation_gap < 0
                                  ? "text-red-600"
                                  : ""
                            }`}
                          >
                            {m.expectation_gap.toFixed(3)}
                          </span>
                          <span
                            className={`text-right tabular-nums ${
                              m.narrative_velocity > 0
                                ? "text-green-600"
                                : m.narrative_velocity < 0
                                  ? "text-red-600"
                                  : ""
                            }`}
                          >
                            {m.narrative_velocity.toFixed(3)}
                          </span>
                          <span
                            className={`text-right tabular-nums ${
                              m.sentiment_divergence > 0
                                ? "text-green-600"
                                : m.sentiment_divergence < 0
                                  ? "text-red-600"
                                  : ""
                            }`}
                          >
                            {m.sentiment_divergence.toFixed(3)}
                          </span>
                          <span
                            className={`text-right font-medium tabular-nums ${
                              m.composite_score > 0
                                ? "text-green-600"
                                : m.composite_score < 0
                                  ? "text-red-600"
                                  : ""
                            }`}
                          >
                            {m.composite_score.toFixed(3)}
                          </span>
                          <span className={`text-right font-medium ${sc.color}`}>
                            {sc.label}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        <TabsContent value="news" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Latest News</CardTitle>
              <CardDescription>
                Recent articles mentioning {ticker}
                {newsData && ` (${newsData.total} total)`}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {isNewsLoading ? (
                <div className="space-y-4">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <div key={i} className="space-y-2">
                      <Skeleton className="h-5 w-3/4" />
                      <Skeleton className="h-3 w-full" />
                      <div className="flex gap-2">
                        <Skeleton className="h-3 w-20" />
                        <Skeleton className="h-3 w-24" />
                        <Skeleton className="h-3 w-16" />
                      </div>
                      {i < 4 && <Separator className="mt-3" />}
                    </div>
                  ))}
                </div>
              ) : newsData && newsData.items.length > 0 ? (
                <div className="space-y-1">
                  {newsData.items.map((article, index) => (
                    <div key={article.id}>
                      <div className="rounded-lg p-3 transition-colors hover:bg-muted/50">
                        <h4 className="text-sm font-medium leading-snug">
                          {article.title}
                        </h4>
                        <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                          <span className="font-medium">{article.source}</span>
                          <span className="text-muted-foreground/40">|</span>
                          <span>
                            {format(
                              new Date(article.published_at),
                              "MMM d, yyyy h:mm a"
                            )}
                          </span>
                          {article.sentiment_score != null && (
                            <>
                              <span className="text-muted-foreground/40">|</span>
                              <span
                                className={`font-medium ${
                                  article.sentiment_score > 0
                                    ? "text-green-600"
                                    : article.sentiment_score < 0
                                      ? "text-red-600"
                                      : "text-muted-foreground"
                                }`}
                              >
                                Sentiment:{" "}
                                {article.sentiment_score > 0 ? "+" : ""}
                                {article.sentiment_score.toFixed(2)}
                              </span>
                            </>
                          )}
                        </div>
                      </div>
                      {index < newsData.items.length - 1 && <Separator />}
                    </div>
                  ))}

                  {/* Pagination */}
                  {newsData.total > newsData.size && (
                    <div className="flex items-center justify-between pt-4">
                      <p className="text-xs text-muted-foreground">
                        Page {newsData.page} of{" "}
                        {Math.ceil(newsData.total / newsData.size)}
                      </p>
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          disabled={newsPage <= 1}
                          onClick={() => setNewsPage((p) => Math.max(1, p - 1))}
                        >
                          Previous
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          disabled={
                            newsPage >=
                            Math.ceil(newsData.total / newsData.size)
                          }
                          onClick={() => setNewsPage((p) => p + 1)}
                        >
                          Next
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-8 text-center">
                  <Newspaper className="mb-2 h-8 w-8 text-muted-foreground/50" />
                  <p className="text-sm text-muted-foreground">
                    No news articles found for {ticker}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
