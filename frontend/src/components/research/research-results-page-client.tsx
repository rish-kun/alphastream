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
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { SentimentBadge } from "@/components/news/sentiment-badge";
import type { SentimentAnalysisEntry } from "@/types/news";

function getArticleSentiment(article: { sentiment_analyses?: SentimentAnalysisEntry[] }): { score: number; hasSentiment: boolean } {
  if (article.sentiment_analyses && article.sentiment_analyses.length > 0) {
    const avgScore = article.sentiment_analyses.reduce((sum, a) => sum + a.sentiment_score, 0) / article.sentiment_analyses.length;
    return { score: avgScore, hasSentiment: true };
  }
  return { score: 0, hasSentiment: false };
}

function calculateOverallSentiment(articles: { sentiment_analyses?: SentimentAnalysisEntry[] }[]): { score: number; label: string; bullish: number; bearish: number; neutral: number } {
  const articlesWithSentiment = articles.filter(a => a.sentiment_analyses && a.sentiment_analyses.length > 0);
  
  if (articlesWithSentiment.length === 0) {
    return { score: 0, label: "neutral", bullish: 0, bearish: 0, neutral: 0 };
  }

  let totalScore = 0;
  let bullish = 0;
  let bearish = 0;
  let neutral = 0;

  for (const article of articlesWithSentiment) {
    const avgScore = article.sentiment_analyses!.reduce((sum, a) => sum + a.sentiment_score, 0) / article.sentiment_analyses!.length;
    totalScore += avgScore;

    if (avgScore >= 0.2) bullish++;
    else if (avgScore <= -0.2) bearish++;
    else neutral++;
  }

  const avgScore = totalScore / articlesWithSentiment.length;
  let label = "neutral";
  if (avgScore >= 0.2) label = "bullish";
  else if (avgScore <= -0.2) label = "bearish";

  return { score: avgScore, label, bullish, bearish, neutral };
}

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
  const analyzed = sentiment.analyzed_articles ?? 0;
  const pending = sentiment.pending_articles ?? 0;
  const total = analyzed + pending;
  const progressPercent = total > 0 ? Math.round((analyzed / total) * 100) : 0;

  const calculatedSentiment = calculateOverallSentiment(result.articles);
  const labelClass =
    calculatedSentiment.label === "bullish"
      ? "bg-green-500/10 text-green-600 border-green-500/20"
      : calculatedSentiment.label === "bearish"
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

      {pending > 0 && (
        <Card className="border-blue-200 bg-blue-50/50">
          <CardContent className="py-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="flex items-center gap-2 text-blue-700">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Analyzing article {analyzed + 1} of {total}
                </span>
                <span className="text-sm font-medium text-blue-700">
                  {progressPercent}% complete
                </span>
              </div>
              <Progress value={progressPercent} className="h-2" />
            </div>
          </CardContent>
        </Card>
      )}

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
              {calculatedSentiment.label}
            </Badge>
            <p className="text-2xl font-bold tabular-nums">
              {calculatedSentiment.score === 0 && pending > 0
                ? "--"
                : calculatedSentiment.score.toFixed(3)}
            </p>
            <div className="space-y-1 text-xs text-muted-foreground">
              <p className="flex items-center gap-1">
                <TrendingUp className="h-3.5 w-3.5 text-green-600" />
                Bullish: {calculatedSentiment.bullish}
              </p>
              <p className="flex items-center gap-1">
                <TrendingDown className="h-3.5 w-3.5 text-red-600" />
                Bearish: {calculatedSentiment.bearish}
              </p>
              <p>Neutral: {calculatedSentiment.neutral}</p>
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
            <Stat label="Articles Found" value={String(result.total_found ?? 0)} />
            <Stat label="New Articles" value={String(result.new_articles ?? 0)} />
            <Stat label="Analyzed" value={String(analyzed)} />
            <Stat
              label="Pending Sentiment"
              value={String(pending)}
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
            {pending > 0
              ? `Sentiment analysis in progress (${pending} pending). This page auto-refreshes.`
              : result.articles.length === 0
                ? ""
                : "Sentiment analysis is complete for all listed articles."}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {result.articles.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No articles were found for this research topic.
            </p>
          ) : (
            result.articles.map((article) => {
              const { score, hasSentiment } = getArticleSentiment(article);
              return (
                <div key={article.id} className="rounded-lg border p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <Link
                        href={`/news/${article.id}`}
                        className="text-sm font-medium hover:underline"
                      >
                        {article.title}
                      </Link>
                      <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
                        <span>{article.source}</span>
                        <span>&middot;</span>
                        <span>{new Date(article.published_at).toLocaleDateString()}</span>
                      </div>
                      {article.summary && (
                        <p className="mt-2 line-clamp-2 text-xs text-muted-foreground">
                          {article.summary.length > 200
                            ? article.summary.slice(0, 200) + "..."
                            : article.summary}
                        </p>
                      )}
                    </div>
                    <div className="shrink-0">
                      {hasSentiment ? (
                        <SentimentBadge score={score} size="sm" showValue={false} />
                      ) : (
                        <Badge variant="outline" className="bg-yellow-500/10 text-yellow-600 border-yellow-500/20 text-[10px]">
                          Analyzing...
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
              );
            })
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
