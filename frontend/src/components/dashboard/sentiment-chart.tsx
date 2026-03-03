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
import type { SentimentOverview } from "@/lib/api";
import { BarChart3 } from "lucide-react";

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


export function SentimentChart() {
  const { data: overview, isLoading, isError } = useQuery({
    queryKey: ["sentiment-overview"],
    queryFn: getSentimentOverview,
    refetchInterval: 120000, // 2 min
  });

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

  if (isError || !overview) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Market Sentiment Trend</CardTitle>
          <CardDescription>
            Aggregate sentiment score from news analysis (-1 to +1)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-12 text-center text-muted-foreground">
            <BarChart3 className="mb-2 h-8 w-8 opacity-50" />
            <p className="text-sm">No sentiment data available</p>
            <p className="text-xs">Data will appear once news articles are analyzed</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const sentimentData = overview;

  const distributionData = [
    { name: "Bullish", count: sentimentData.bullish_count, fill: "hsl(142 76% 36%)" },
    { name: "Bearish", count: sentimentData.bearish_count, fill: "hsl(0 84% 60%)" },
    { name: "Neutral", count: sentimentData.neutral_count, fill: "hsl(45 93% 47%)" },
  ];



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
              {sentimentData.overall_score !== undefined && sentimentData.overall_score !== null
                ? `${sentimentData.overall_score > 0 ? "+" : ""}${sentimentData.overall_score.toFixed(2)}`
                : "N/A"}
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
            <div className="flex flex-col items-center justify-center h-[300px] text-center text-muted-foreground">
              <BarChart3 className="mb-2 h-8 w-8 opacity-50" />
              <p className="text-sm">Sentiment trend data coming soon</p>
              <p className="text-xs">Intraday trend tracking is being developed</p>
            </div>
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
