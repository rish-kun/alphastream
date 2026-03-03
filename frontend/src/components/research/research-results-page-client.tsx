"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
  BarChart3,
  Loader2,
  Newspaper,
  Sparkles,
  TrendingDown,
  TrendingUp,
} from "lucide-react";

import { getResearchResult, getResearchStatus } from "@/lib/api";
import { NewsCard } from "@/components/news/news-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

interface ResearchResultsPageClientProps {
  taskId: string;
}

export function ResearchResultsPageClient({
  taskId,
}: ResearchResultsPageClientProps) {
  const searchParams = useSearchParams();
  const topic = searchParams.get("topic");
  const statusQuery = useQuery({
    queryKey: ["research-status-gate", taskId],
    queryFn: () => getResearchStatus(taskId),
    refetchInterval: (query) => {
      const state = query.state.data?.status;
      if (state === "SUCCESS" || state === "FAILURE") return false;
      return 2500;
    },
  });
  const taskStatus = statusQuery.data?.status;
  const stage =
    typeof statusQuery.data?.progress?.stage === "string"
      ? statusQuery.data.progress.stage
      : "Research in progress";

  const resultQuery = useQuery({
    queryKey: ["research-results", taskId],
    queryFn: () => getResearchResult(taskId),
    enabled: taskStatus === "SUCCESS",
    refetchInterval: (query) => {
      const pending = query.state.data?.sentiment?.pending_articles ?? 0;
      return pending > 0 ? 5000 : false;
    },
  });

  if (
    statusQuery.isLoading ||
    taskStatus === "PENDING" ||
    taskStatus === "PROGRESS" ||
    taskStatus === "STARTED" ||
    !taskStatus
  ) {
    return (
      <div className="mx-auto max-w-4xl space-y-4">
        <h1 className="text-2xl font-bold">Deep Research Results</h1>
        <Card>
          <CardContent className="py-8">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              {stage}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (taskStatus === "FAILURE") {
    return (
      <div className="mx-auto max-w-4xl space-y-4">
        <h1 className="text-2xl font-bold">Deep Research Results</h1>
        <Card>
          <CardHeader>
            <CardTitle>Research Failed</CardTitle>
            <CardDescription>
              {statusQuery.data?.error ?? "Unable to complete this research task"}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild variant="outline">
              <Link href="/news">Back to News</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (resultQuery.isLoading) {
    return (
      <div className="mx-auto max-w-4xl space-y-4">
        <h1 className="text-2xl font-bold">Deep Research Results</h1>
        <Card>
          <CardContent className="py-8">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading final results...
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (resultQuery.isError || !resultQuery.data) {
    return (
      <div className="mx-auto max-w-4xl space-y-4">
        <h1 className="text-2xl font-bold">Deep Research Results</h1>
        <Card>
          <CardHeader>
            <CardTitle>Unable to load results</CardTitle>
            <CardDescription>
              {resultQuery.error instanceof Error
                ? resultQuery.error.message
                : "Result is not available"}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild variant="outline">
              <Link href="/news">Back to News</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const result = resultQuery.data;
  const sentiment = result.sentiment;
  const labelClass =
    sentiment.overall_label === "bullish"
      ? "bg-green-500/10 text-green-600 border-green-500/20"
      : sentiment.overall_label === "bearish"
      ? "bg-red-500/10 text-red-600 border-red-500/20"
      : "bg-slate-500/10 text-slate-700 border-slate-500/20";

  return (
    <div className="mx-auto max-w-4xl space-y-5">
      <div className="space-y-1">
        <h1 className="text-2xl font-bold">Deep Research Results</h1>
        <p className="text-sm text-muted-foreground">
          {topic
            ? `Topic: ${topic}`
            : result.topic
              ? `Topic: ${result.topic}`
              : "Research summary"}
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card className="md:col-span-1">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Sparkles className="h-4 w-4" />
              Overall Sentiment
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Badge variant="outline" className={labelClass}>
              {sentiment.overall_label}
            </Badge>
            <p className="text-2xl font-bold tabular-nums">
              {sentiment.overall_score == null
                ? "--"
                : sentiment.overall_score.toFixed(3)}
            </p>
            <div className="space-y-1 text-xs text-muted-foreground">
              <p className="flex items-center gap-1">
                <TrendingUp className="h-3.5 w-3.5 text-green-600" />
                Bullish: {sentiment.bullish_count}
              </p>
              <p className="flex items-center gap-1">
                <TrendingDown className="h-3.5 w-3.5 text-red-600" />
                Bearish: {sentiment.bearish_count}
              </p>
              <p>Neutral: {sentiment.neutral_count}</p>
            </div>
          </CardContent>
        </Card>

        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <BarChart3 className="h-4 w-4" />
              Coverage
            </CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-2 gap-3 text-sm">
            <Stat label="Articles Found" value={String(result.total_found)} />
            <Stat label="New Articles" value={String(result.new_articles)} />
            <Stat label="Analyzed" value={String(sentiment.analyzed_articles)} />
            <Stat
              label="Pending Sentiment"
              value={String(sentiment.pending_articles)}
            />
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Newspaper className="h-4 w-4" />
            Researched Articles
          </CardTitle>
          <CardDescription>
            {sentiment.pending_articles > 0
              ? "Sentiment is still updating for some articles. This page auto-refreshes."
              : "Sentiment analysis is complete for all listed articles."}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {result.articles.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No new articles were inserted by this research run.
            </p>
          ) : (
            result.articles.map((article) => (
              <NewsCard key={article.id} article={article} variant="compact" />
            ))
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border p-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-lg font-semibold tabular-nums">{value}</p>
    </div>
  );
}
