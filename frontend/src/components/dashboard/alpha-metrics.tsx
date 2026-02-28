"use client";

import { useQuery } from "@tanstack/react-query";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import {
  TrendingUp,
  TrendingDown,
  Activity,
  BarChart3,
  Minus,
} from "lucide-react";
import { getSentimentOverview, getTopAlphaSignals } from "@/lib/api";
import type { AlphaMetric, SentimentOverview } from "@/types/sentiment";
import type { SignalType } from "@/types/stock";

// ─── Signal Helpers ──────────────────────────────────────────────────────────

const signalConfig: Record<
  SignalType,
  { label: string; color: string; bgColor: string; icon: typeof TrendingUp }
> = {
  strong_buy: {
    label: "Strong Buy",
    color: "text-green-700 dark:text-green-400",
    bgColor: "bg-green-500/10 border-green-500/20",
    icon: TrendingUp,
  },
  buy: {
    label: "Buy",
    color: "text-green-600 dark:text-green-500",
    bgColor: "bg-green-500/10 border-green-500/20",
    icon: TrendingUp,
  },
  hold: {
    label: "Hold",
    color: "text-yellow-600 dark:text-yellow-400",
    bgColor: "bg-yellow-500/10 border-yellow-500/20",
    icon: Minus,
  },
  sell: {
    label: "Sell",
    color: "text-red-600 dark:text-red-500",
    bgColor: "bg-red-500/10 border-red-500/20",
    icon: TrendingDown,
  },
  strong_sell: {
    label: "Strong Sell",
    color: "text-red-700 dark:text-red-400",
    bgColor: "bg-red-500/10 border-red-500/20",
    icon: TrendingDown,
  },
};

function getSignalInfo(signal: SignalType) {
  return signalConfig[signal] ?? signalConfig.hold;
}

function formatConviction(conviction: number): string {
  return `${(conviction * 100).toFixed(0)}%`;
}

function formatScore(score: number): string {
  const sign = score > 0 ? "+" : "";
  return `${sign}${score.toFixed(2)}`;
}

// ─── Summary Cards ───────────────────────────────────────────────────────────

const fallbackOverview: SentimentOverview = {
  market_sentiment: 0.32,
  bullish_count: 42,
  bearish_count: 18,
  neutral_count: 26,
  total_articles: 86,
  sentiment_trend: [],
  sectors: [],
  updated_at: new Date().toISOString(),
};

function SummaryCards({ overview }: { overview: SentimentOverview }) {
  const metrics = [
    {
      title: "Market Sentiment",
      value: formatScore(overview.market_sentiment),
      description:
        overview.market_sentiment > 0.2
          ? "Moderately Bullish"
          : overview.market_sentiment < -0.2
            ? "Moderately Bearish"
            : "Neutral",
      icon: Activity,
      trend: overview.market_sentiment >= 0 ? ("up" as const) : ("down" as const),
    },
    {
      title: "Total Articles",
      value: String(overview.total_articles ?? "—"),
      description: "Analyzed in last 24h",
      icon: BarChart3,
      trend: "up" as const,
    },
    {
      title: "Bullish Stories",
      value: String(overview.bullish_count),
      description: "In last 24 hours",
      icon: TrendingUp,
      trend: "up" as const,
    },
    {
      title: "Bearish Stories",
      value: String(overview.bearish_count),
      description: "In last 24 hours",
      icon: TrendingDown,
      trend: "down" as const,
    },
  ];

  return (
    <>
      {metrics.map((metric) => (
        <Card key={metric.title}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{metric.title}</CardTitle>
            <metric.icon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metric.value}</div>
            <p className="text-xs text-muted-foreground">{metric.description}</p>
          </CardContent>
        </Card>
      ))}
    </>
  );
}

// ─── Alpha Signals Table ─────────────────────────────────────────────────────

function AlphaSignalsTable({ signals }: { signals: AlphaMetric[] }) {
  if (signals.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-center text-muted-foreground">
        <BarChart3 className="mb-2 h-8 w-8 opacity-50" />
        <p className="text-sm">No alpha signals available</p>
        <p className="text-xs">Signals will appear when analysis is complete</p>
      </div>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Stock</TableHead>
          <TableHead>Signal</TableHead>
          <TableHead className="text-right">Score</TableHead>
          <TableHead className="text-right">Conviction</TableHead>
          <TableHead className="hidden text-right md:table-cell">
            Exp. Gap
          </TableHead>
          <TableHead className="hidden text-right lg:table-cell">
            Narrative V.
          </TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {signals.map((metric) => {
          const info = getSignalInfo(metric.signal);
          const SignalIcon = info.icon;
          return (
            <TableRow key={metric.id}>
              <TableCell>
                <div>
                  <p className="font-medium">
                    {metric.ticker ?? metric.sector ?? "Market"}
                  </p>
                  {metric.company_name && (
                    <p className="text-xs text-muted-foreground">
                      {metric.company_name}
                    </p>
                  )}
                </div>
              </TableCell>
              <TableCell>
                <Badge variant="outline" className={info.bgColor}>
                  <SignalIcon className={`mr-1 h-3 w-3 ${info.color}`} />
                  <span className={info.color}>{info.label}</span>
                </Badge>
              </TableCell>
              <TableCell className="text-right">
                <span
                  className={`font-mono font-semibold ${
                    metric.composite_score > 0
                      ? "text-green-600 dark:text-green-400"
                      : metric.composite_score < 0
                        ? "text-red-600 dark:text-red-400"
                        : "text-muted-foreground"
                  }`}
                >
                  {formatScore(metric.composite_score)}
                </span>
              </TableCell>
              <TableCell className="text-right">
                <span className="font-mono text-sm">
                  {formatConviction(metric.conviction)}
                </span>
              </TableCell>
              <TableCell className="hidden text-right md:table-cell">
                <span className="font-mono text-sm text-muted-foreground">
                  {formatScore(metric.expectation_gap)}
                </span>
              </TableCell>
              <TableCell className="hidden text-right lg:table-cell">
                <span className="font-mono text-sm text-muted-foreground">
                  {formatScore(metric.narrative_velocity)}
                </span>
              </TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
}

// ─── Main Export ──────────────────────────────────────────────────────────────

export function AlphaMetrics() {
  const { data: overview, isLoading: overviewLoading } = useQuery({
    queryKey: ["sentiment-overview"],
    queryFn: getSentimentOverview,
    refetchInterval: 120000,
  });

  const { data: signals, isLoading: signalsLoading } = useQuery({
    queryKey: ["alpha-signals"],
    queryFn: () => getTopAlphaSignals(10),
    refetchInterval: 120000,
  });

  const sentimentData = overview ?? fallbackOverview;

  if (overviewLoading) {
    return (
      <>
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-4 w-4 rounded" />
            </CardHeader>
            <CardContent>
              <Skeleton className="mb-1 h-7 w-16" />
              <Skeleton className="h-3 w-32" />
            </CardContent>
          </Card>
        ))}
      </>
    );
  }

  return (
    <>
      <SummaryCards overview={sentimentData} />

      {/* Alpha Signals Table — spans full width below the summary cards */}
      <div className="col-span-full">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Top Alpha Signals
            </CardTitle>
            <CardDescription>
              Highest conviction trading signals from sentiment analysis
            </CardDescription>
          </CardHeader>
          <CardContent>
            {signalsLoading ? (
              <div className="space-y-3">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Skeleton key={i} className="h-12 w-full" />
                ))}
              </div>
            ) : (
              <AlphaSignalsTable signals={signals ?? []} />
            )}
          </CardContent>
        </Card>
      </div>
    </>
  );
}
