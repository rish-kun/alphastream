"use client";

import { useQuery } from "@tanstack/react-query";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  XAxis,
  YAxis,
} from "recharts";
import { getSentimentOverview } from "@/lib/api";
import type { SentimentOverview, SentimentTrendPoint } from "@/types/sentiment";

const sentimentLineConfig = {
  sentiment: {
    label: "Sentiment",
    color: "hsl(var(--chart-2))",
  },
  volume: {
    label: "Volume",
    color: "hsl(var(--chart-4))",
  },
};

const distributionConfig = {
  bullish: {
    label: "Bullish",
    color: "hsl(142 76% 36%)",
  },
  bearish: {
    label: "Bearish",
    color: "hsl(0 84% 60%)",
  },
  neutral: {
    label: "Neutral",
    color: "hsl(45 93% 47%)",
  },
};

function formatTrendTime(timestamp: string): string {
  try {
    const date = new Date(timestamp);
    return date.toLocaleTimeString("en-IN", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });
  } catch {
    return timestamp;
  }
}

// Fallback data when API is unavailable
const fallbackTrend: SentimentTrendPoint[] = [
  { timestamp: "2026-02-27T09:15:00", sentiment: 0.12, volume: 15 },
  { timestamp: "2026-02-27T09:45:00", sentiment: 0.18, volume: 22 },
  { timestamp: "2026-02-27T10:15:00", sentiment: 0.24, volume: 18 },
  { timestamp: "2026-02-27T10:45:00", sentiment: 0.15, volume: 25 },
  { timestamp: "2026-02-27T11:15:00", sentiment: -0.05, volume: 12 },
  { timestamp: "2026-02-27T11:45:00", sentiment: -0.12, volume: 20 },
  { timestamp: "2026-02-27T12:15:00", sentiment: -0.08, volume: 8 },
  { timestamp: "2026-02-27T12:45:00", sentiment: 0.02, volume: 14 },
  { timestamp: "2026-02-27T13:15:00", sentiment: 0.1, volume: 19 },
  { timestamp: "2026-02-27T13:45:00", sentiment: 0.22, volume: 24 },
  { timestamp: "2026-02-27T14:15:00", sentiment: 0.28, volume: 30 },
  { timestamp: "2026-02-27T14:45:00", sentiment: 0.35, volume: 27 },
  { timestamp: "2026-02-27T15:15:00", sentiment: 0.32, volume: 21 },
];

const fallbackOverview: SentimentOverview = {
  market_sentiment: 0.32,
  bullish_count: 42,
  bearish_count: 18,
  neutral_count: 26,
  total_articles: 86,
  sentiment_trend: fallbackTrend,
  sectors: [],
  updated_at: new Date().toISOString(),
};

export function SentimentChart() {
  const { data: overview, isLoading } = useQuery({
    queryKey: ["sentiment-overview"],
    queryFn: getSentimentOverview,
    refetchInterval: 120000, // 2 min
  });

  const sentimentData = overview ?? fallbackOverview;

  const trendData = (sentimentData.sentiment_trend ?? fallbackTrend).map(
    (point) => ({
      time: formatTrendTime(point.timestamp),
      sentiment: point.sentiment,
      volume: point.volume,
    })
  );

  const distributionData = [
    { name: "Bullish", count: sentimentData.bullish_count, fill: "hsl(142 76% 36%)" },
    { name: "Bearish", count: sentimentData.bearish_count, fill: "hsl(0 84% 60%)" },
    { name: "Neutral", count: sentimentData.neutral_count, fill: "hsl(45 93% 47%)" },
  ];

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Market Sentiment Trend</CardTitle>
          <CardDescription>Loading sentiment data...</CardDescription>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[300px] w-full" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Market Sentiment Trend</CardTitle>
            <CardDescription>
              Aggregate sentiment score from news analysis (-1 to +1)
            </CardDescription>
          </div>
          <div className="text-right">
            <p className="text-2xl font-bold">
              {sentimentData.market_sentiment > 0 ? "+" : ""}
              {sentimentData.market_sentiment.toFixed(2)}
            </p>
            <p className="text-xs text-muted-foreground">
              {sentimentData.total_articles ?? "—"} articles analyzed
            </p>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="trend">
          <TabsList>
            <TabsTrigger value="trend">Trend</TabsTrigger>
            <TabsTrigger value="distribution">Distribution</TabsTrigger>
          </TabsList>
          <TabsContent value="trend" className="mt-4">
            <ChartContainer config={sentimentLineConfig} className="h-[300px] w-full">
              <AreaChart data={trendData}>
                <defs>
                  <linearGradient
                    id="sentimentGrad"
                    x1="0"
                    y1="0"
                    x2="0"
                    y2="1"
                  >
                    <stop
                      offset="5%"
                      stopColor="hsl(var(--chart-2))"
                      stopOpacity={0.3}
                    />
                    <stop
                      offset="95%"
                      stopColor="hsl(var(--chart-2))"
                      stopOpacity={0}
                    />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis
                  domain={[-1, 1]}
                  fontSize={12}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(v) => v.toFixed(1)}
                />
                <ChartTooltip content={<ChartTooltipContent />} />
                <Area
                  type="monotone"
                  dataKey="sentiment"
                  stroke="var(--color-sentiment)"
                  fill="url(#sentimentGrad)"
                  strokeWidth={2}
                />
              </AreaChart>
            </ChartContainer>
          </TabsContent>
          <TabsContent value="distribution" className="mt-4">
            <ChartContainer config={distributionConfig} className="h-[300px] w-full">
              <BarChart data={distributionData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis fontSize={12} tickLine={false} axisLine={false} />
                <ChartTooltip content={<ChartTooltipContent />} />
                <Bar dataKey="count" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ChartContainer>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
