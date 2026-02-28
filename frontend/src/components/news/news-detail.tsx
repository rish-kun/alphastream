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
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { SentimentBadge } from "@/components/news/sentiment-badge";
import {
  ArrowLeft,
  ExternalLink,
  Clock,
  Newspaper,
  TrendingUp,
  BarChart3,
  AlertCircle,
} from "lucide-react";
import Link from "next/link";
import { getNewsArticle } from "@/lib/api";
import type { NewsArticleDetail, SentimentAnalysisEntry } from "@/types/news";

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-IN", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function timeAgo(dateStr: string): string {
  const now = Date.now();
  const date = new Date(dateStr).getTime();
  const diffMs = now - date;
  const minutes = Math.floor(diffMs / 60_000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d ago`;
  return `${Math.floor(days / 7)}w ago`;
}

interface NewsDetailProps {
  id: string;
}

export function NewsDetail({ id }: NewsDetailProps) {
  const {
    data: article,
    isLoading,
    error,
  } = useQuery<NewsArticleDetail>({
    queryKey: ["article", id],
    queryFn: () => getNewsArticle(id),
  });

  if (isLoading) return <NewsDetailSkeleton />;

  if (error) {
    return (
      <div className="space-y-6">
        <BackButton />
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <AlertCircle className="h-12 w-12 text-muted-foreground" />
            <h3 className="mt-4 text-lg font-semibold">
              Failed to load article
            </h3>
            <p className="mt-1 text-sm text-muted-foreground">
              {error instanceof Error ? error.message : "An error occurred"}
            </p>
            <Button variant="outline" className="mt-4" asChild>
              <Link href="/news">Back to News</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!article) return null;

  const primarySentiment = article.sentiment_analyses?.[0];
  const avgSentiment =
    article.sentiment_analyses?.length > 0
      ? article.sentiment_analyses.reduce(
          (sum, s) => sum + s.sentiment_score,
          0
        ) / article.sentiment_analyses.length
      : null;

  return (
    <div className="space-y-6">
      <BackButton />

      {/* Main article card */}
      <Card>
        <CardHeader className="space-y-4">
          <div className="flex items-center gap-3 text-sm text-muted-foreground">
            <div className="flex items-center gap-1.5">
              <Newspaper className="h-4 w-4" />
              <span className="font-medium">{article.source}</span>
            </div>
            <span>&middot;</span>
            <div className="flex items-center gap-1">
              <Clock className="h-3.5 w-3.5" />
              <span>{timeAgo(article.published_at)}</span>
            </div>
            <span className="hidden sm:inline">&middot;</span>
            <span className="hidden text-xs sm:inline">
              {formatDate(article.published_at)}
            </span>
          </div>

          <CardTitle className="text-2xl leading-tight md:text-3xl">
            {article.title}
          </CardTitle>

          <div className="flex flex-wrap items-center gap-2">
            {article.category && (
              <Badge variant="outline">{article.category}</Badge>
            )}
            {avgSentiment !== null && (
              <SentimentBadge score={avgSentiment} size="lg" />
            )}
          </div>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Article content */}
          <div className="prose prose-sm dark:prose-invert max-w-none">
            {article.full_text ? (
              article.full_text.split("\n").map((paragraph, i) =>
                paragraph.trim() ? (
                  <p key={i} className="text-sm leading-relaxed text-foreground">
                    {paragraph}
                  </p>
                ) : null
              )
            ) : article.summary ? (
              <p className="text-sm leading-relaxed text-foreground">
                {article.summary}
              </p>
            ) : (
              <p className="text-sm italic text-muted-foreground">
                Full article text is not available.
              </p>
            )}
          </div>

          <Separator />

          {/* Sentiment Analysis Section */}
          {article.sentiment_analyses?.length > 0 && (
            <>
              <SentimentSection analyses={article.sentiment_analyses} />
              <Separator />
            </>
          )}

          {/* Mentioned Stocks */}
          {article.mentions?.length > 0 && (
            <>
              <div>
                <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold">
                  <TrendingUp className="h-4 w-4" />
                  Mentioned Stocks
                </h3>
                <div className="flex flex-wrap gap-2">
                  {article.mentions.map((mention) => (
                    <Link
                      key={mention.ticker}
                      href={`/stocks/${mention.ticker}`}
                    >
                      <Badge
                        variant="secondary"
                        className="cursor-pointer gap-1.5 px-3 py-1.5 transition-colors hover:bg-secondary/80"
                      >
                        <span className="font-mono font-semibold">
                          {mention.ticker}
                        </span>
                        <span className="text-muted-foreground">
                          {mention.company_name}
                        </span>
                        {mention.relevance_score > 0 && (
                          <span className="ml-1 text-[10px] text-muted-foreground">
                            {(mention.relevance_score * 100).toFixed(0)}%
                          </span>
                        )}
                      </Badge>
                    </Link>
                  ))}
                </div>
              </div>
              <Separator />
            </>
          )}

          {/* External link */}
          {article.url && (
            <Button variant="outline" className="gap-2" asChild>
              <a
                href={article.url}
                target="_blank"
                rel="noopener noreferrer"
              >
                <ExternalLink className="h-4 w-4" />
                View Original Article
              </a>
            </Button>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function SentimentSection({
  analyses,
}: {
  analyses: SentimentAnalysisEntry[];
}) {
  const primary = analyses[0];
  const hasMultiple = analyses.length > 1;

  return (
    <div>
      <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold">
        <BarChart3 className="h-4 w-4" />
        Sentiment Analysis
      </h3>

      <div className="grid gap-3 sm:grid-cols-3">
        {/* Score */}
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Sentiment Score</CardDescription>
          </CardHeader>
          <CardContent>
            <SentimentBadge score={primary.sentiment_score} size="lg" />
          </CardContent>
        </Card>

        {/* Confidence */}
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Confidence</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <span className="text-lg font-bold">
              {(primary.confidence * 100).toFixed(0)}%
            </span>
            <Progress value={primary.confidence * 100} className="h-2" />
          </CardContent>
        </Card>

        {/* Impact Timeline */}
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Impact Timeline</CardDescription>
          </CardHeader>
          <CardContent>
            <span className="text-lg font-semibold capitalize">
              {primary.impact_timeline || "Short-term"}
            </span>
          </CardContent>
        </Card>
      </div>

      {/* Explanation */}
      {primary.explanation && (
        <Card className="mt-3">
          <CardContent className="py-3">
            <p className="text-sm text-muted-foreground">
              {primary.explanation}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Model comparison if multiple analyses */}
      {hasMultiple && (
        <div className="mt-4">
          <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Model Comparison
          </h4>
          <div className="space-y-2">
            {analyses.map((analysis, i) => (
              <div
                key={i}
                className="flex items-center justify-between rounded-lg border px-3 py-2"
              >
                <span className="text-sm font-medium">
                  {analysis.model || `Model ${i + 1}`}
                </span>
                <div className="flex items-center gap-3">
                  <SentimentBadge
                    score={analysis.sentiment_score}
                    size="sm"
                  />
                  <span className="text-xs text-muted-foreground">
                    {(analysis.confidence * 100).toFixed(0)}% conf.
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function BackButton() {
  return (
    <div className="flex items-center gap-4">
      <Button variant="ghost" size="sm" className="gap-2" asChild>
        <Link href="/news">
          <ArrowLeft className="h-4 w-4" />
          Back to News
        </Link>
      </Button>
    </div>
  );
}

function NewsDetailSkeleton() {
  return (
    <div className="space-y-6">
      <BackButton />
      <Card>
        <CardHeader className="space-y-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Skeleton className="h-4 w-24" />
            <span>&middot;</span>
            <Skeleton className="h-4 w-20" />
          </div>
          <Skeleton className="h-9 w-3/4" />
          <div className="flex items-center gap-2">
            <Skeleton className="h-6 w-16 rounded-md" />
            <Skeleton className="h-6 w-28 rounded-md" />
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-3">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-5/6" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-2/3" />
          </div>

          <Separator />

          <div>
            <h3 className="mb-3 text-sm font-semibold">Sentiment Analysis</h3>
            <div className="grid gap-3 sm:grid-cols-3">
              {[1, 2, 3].map((i) => (
                <Card key={i}>
                  <CardHeader className="pb-2">
                    <Skeleton className="h-3 w-20" />
                  </CardHeader>
                  <CardContent>
                    <Skeleton className="h-6 w-16" />
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>

          <Separator />

          <div>
            <h3 className="mb-3 text-sm font-semibold">Mentioned Stocks</h3>
            <div className="flex flex-wrap gap-2">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-8 w-28 rounded-md" />
              ))}
            </div>
          </div>

          <Skeleton className="h-10 w-48" />
        </CardContent>
      </Card>
    </div>
  );
}
