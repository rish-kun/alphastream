"use client";

import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SentimentBadge } from "@/components/news/sentiment-badge";
import { Clock, Newspaper } from "lucide-react";
import type { NewsArticleListItem, TrendingArticle } from "@/types/news";

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

  const weeks = Math.floor(days / 7);
  if (weeks < 4) return `${weeks}w ago`;

  const months = Math.floor(days / 30);
  return `${months}mo ago`;
}

/** Props when used with full API data */
interface NewsCardApiProps {
  article: NewsArticleListItem | TrendingArticle;
  variant?: "default" | "compact" | "trending";
}

/** Props when used with manual values (backward compat) */
interface NewsCardManualProps {
  title: string;
  source: string;
  publishedAt: string;
  summary?: string;
  sentimentScore: number;
  category?: string;
  tickers?: string[];
  id?: string;
  variant?: "default" | "compact" | "trending";
}

type NewsCardProps = NewsCardApiProps | NewsCardManualProps;

function isApiProps(props: NewsCardProps): props is NewsCardApiProps {
  return "article" in props;
}

export function NewsCard(props: NewsCardProps) {
  if (isApiProps(props)) {
    return <NewsCardFromArticle {...props} />;
  }
  return <NewsCardFromManual {...props} />;
}

function NewsCardFromArticle({
  article,
  variant = "default",
}: NewsCardApiProps) {
  const sentimentScore =
    "sentiment_analyses" in article && article.sentiment_analyses?.length > 0
      ? article.sentiment_analyses[0].sentiment_score
      : "sentiment_score" in article
        ? (article.sentiment_score ?? 0)
        : 0;

  const category =
    "category" in article ? (article as NewsArticleListItem).category : null;
  const summary =
    "summary" in article ? (article as NewsArticleListItem).summary : null;
  const tickers = article.mentions?.map((m) => m.ticker) ?? [];

  if (variant === "trending") {
    return (
      <Link href={`/news/${article.id}`} className="block">
        <Card className="h-full min-w-[280px] transition-all hover:bg-muted/50 hover:shadow-md">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between gap-2">
              <Badge variant="secondary" className="text-[10px]">
                {article.source}
              </Badge>
              <SentimentBadge score={sentimentScore} size="sm" />
            </div>
            <CardTitle className="line-clamp-2 text-sm leading-snug">
              {article.title}
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Clock className="h-3 w-3" />
              {timeAgo(article.published_at)}
            </div>
            {tickers.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1">
                {tickers.slice(0, 3).map((t) => (
                  <Badge key={t} variant="outline" className="text-[10px] px-1.5 py-0 font-mono">
                    {t}
                  </Badge>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </Link>
    );
  }

  if (variant === "compact") {
    return (
      <Link href={`/news/${article.id}`} className="block">
        <div className="flex items-start gap-3 rounded-lg border p-3 transition-colors hover:bg-muted/50">
          <div className="flex-1 min-w-0">
            <p className="line-clamp-1 text-sm font-medium leading-tight">
              {article.title}
            </p>
            <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
              <span>{article.source}</span>
              <span>&middot;</span>
              <span>{timeAgo(article.published_at)}</span>
            </div>
          </div>
          <SentimentBadge score={sentimentScore} size="sm" showValue={false} />
        </div>
      </Link>
    );
  }

  return (
    <Link href={`/news/${article.id}`} className="block">
      <Card className="transition-all hover:bg-muted/50 hover:shadow-md">
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0 flex-1 space-y-1">
              <CardTitle className="text-lg leading-tight">
                {article.title}
              </CardTitle>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Newspaper className="h-3 w-3 shrink-0" />
                <span className="font-medium">{article.source}</span>
                <span>&middot;</span>
                <span className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {timeAgo(article.published_at)}
                </span>
              </div>
            </div>
            <div className="flex shrink-0 items-center gap-2">
              {category && <Badge variant="outline">{category}</Badge>}
              <SentimentBadge score={sentimentScore} />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {summary && (
            <p className="line-clamp-2 text-sm text-muted-foreground">
              {summary}
            </p>
          )}
          {tickers.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {tickers.map((t) => (
                <Badge
                  key={t}
                  variant="secondary"
                  className="font-mono text-xs"
                >
                  {t}
                </Badge>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </Link>
  );
}

/** Backward-compatible card with manual props */
function NewsCardFromManual({
  title,
  source,
  publishedAt,
  summary,
  sentimentScore,
  category,
  tickers,
  id,
}: NewsCardManualProps) {
  const content = (
    <Card className="transition-all hover:bg-muted/50 hover:shadow-md">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0 flex-1 space-y-1">
            <CardTitle className="text-lg leading-tight">{title}</CardTitle>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Newspaper className="h-3 w-3 shrink-0" />
              <span className="font-medium">{source}</span>
              <span>&middot;</span>
              <span className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {publishedAt}
              </span>
            </div>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            {category && <Badge variant="outline">{category}</Badge>}
            <SentimentBadge score={sentimentScore} />
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {summary && (
          <p className="line-clamp-2 text-sm text-muted-foreground">
            {summary}
          </p>
        )}
        {tickers && tickers.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1.5">
            {tickers.map((t) => (
              <Badge key={t} variant="secondary" className="font-mono text-xs">
                {t}
              </Badge>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );

  if (id) {
    return (
      <Link href={`/news/${id}`} className="block">
        {content}
      </Link>
    );
  }

  return content;
}
