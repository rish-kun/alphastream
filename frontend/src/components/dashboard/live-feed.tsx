"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { Newspaper, Clock } from "lucide-react";
import { getNewsFeed } from "@/lib/api";
import { useWebSocketChannel } from "@/hooks/use-websocket";
import type { NewsArticleListItem } from "@/types/news";

const sentimentColors: Record<string, string> = {
  bullish: "bg-green-500/10 text-green-600 border-green-500/20",
  bearish: "bg-red-500/10 text-red-600 border-red-500/20",
  neutral: "bg-yellow-500/10 text-yellow-600 border-yellow-500/20",
};

function formatTimeAgo(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);

  if (diffMins < 1) return "just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays}d ago`;
}

function getAvgSentiment(
  analyses: { sentiment_score: number }[]
): number | null {
  if (!analyses || analyses.length === 0) return null;
  const sum = analyses.reduce((acc, a) => acc + a.sentiment_score, 0);
  return sum / analyses.length;
}

function getSentimentLabel(score: number | null): "bullish" | "bearish" | "neutral" {
  if (score === null) return "neutral";
  if (score > 0.15) return "bullish";
  if (score < -0.15) return "bearish";
  return "neutral";
}

export function LiveFeed() {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);

  // Fetch initial news feed
  const { data, isLoading, error } = useQuery({
    queryKey: ["news-feed"],
    queryFn: () => getNewsFeed({ page: 1, size: 30 }),
    refetchInterval: 60000, // Refetch every minute
  });

  // Listen for real-time news updates via WebSocket
  const { messages: wsMessages } = useWebSocketChannel<NewsArticleListItem>(
    "news",
    "news_update"
  );

  // Merge WebSocket messages with API data
  const allItems: NewsArticleListItem[] = (() => {
    const apiItems = data?.items ?? [];
    const wsIds = new Set(wsMessages.map((m) => m.id));
    const deduped = apiItems.filter((item) => !wsIds.has(item.id));
    return [...wsMessages, ...deduped].slice(0, 50);
  })();

  // Auto-scroll to top when new items arrive via WS
  useEffect(() => {
    if (autoScroll && wsMessages.length > 0 && scrollRef.current) {
      scrollRef.current.scrollTop = 0;
    }
  }, [wsMessages.length, autoScroll]);

  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    const target = e.target as HTMLDivElement;
    setAutoScroll(target.scrollTop < 10);
  }, []);

  if (isLoading) {
    return (
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Newspaper className="h-5 w-5" />
            Live News Feed
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="space-y-2 p-3">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-3 w-1/2" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2">
          <Newspaper className="h-5 w-5" />
          Live News Feed
        </CardTitle>
        <div className="flex items-center gap-2">
          {wsMessages.length > 0 && (
            <Badge variant="secondary" className="text-xs">
              {wsMessages.length} new
            </Badge>
          )}
          <Badge variant="outline" className="gap-1">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-green-500" />
            </span>
            Live
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[400px]" onScrollCapture={handleScroll}>
          <div ref={scrollRef} className="space-y-1">
            {error && allItems.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8 text-center text-muted-foreground">
                <Newspaper className="mb-2 h-8 w-8 opacity-50" />
                <p className="text-sm">Unable to load news feed</p>
                <p className="text-xs">Will retry automatically</p>
              </div>
            ) : allItems.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8 text-center text-muted-foreground">
                <Newspaper className="mb-2 h-8 w-8 opacity-50" />
                <p className="text-sm">No news articles yet</p>
                <p className="text-xs">
                  New articles will appear here in real-time
                </p>
              </div>
            ) : (
              allItems.map((item, index) => {
                const avgScore = getAvgSentiment(item.sentiment_analyses);
                const label = getSentimentLabel(avgScore);
                const confidence =
                  item.sentiment_analyses?.[0]?.confidence ?? null;
                const tickers = item.mentions?.map((m) => m.ticker) ?? [];

                return (
                  <div key={item.id}>
                    <div className="flex items-start gap-3 rounded-lg p-3 transition-colors hover:bg-muted/50">
                      <div className="flex-1 space-y-1">
                        <p className="text-sm font-medium leading-tight">
                          {item.title}
                        </p>
                        <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                          <span className="font-medium">{item.source}</span>
                          <span className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {formatTimeAgo(item.published_at)}
                          </span>
                          {tickers.length > 0 && (
                            <div className="flex gap-1">
                              {tickers.slice(0, 3).map((ticker) => (
                                <Badge
                                  key={ticker}
                                  variant="secondary"
                                  className="px-1 py-0 text-[10px]"
                                >
                                  {ticker}
                                </Badge>
                              ))}
                              {tickers.length > 3 && (
                                <span className="text-[10px]">
                                  +{tickers.length - 3}
                                </span>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                      <div className="flex flex-col items-end gap-1">
                        <Badge
                          variant="outline"
                          className={
                            sentimentColors[label] ?? sentimentColors.neutral
                          }
                        >
                          {label}
                        </Badge>
                        {confidence !== null && confidence !== undefined && (
                          <span className="text-[10px] text-muted-foreground">
                            {(confidence * 100).toFixed(0)}% conf
                          </span>
                        )}
                      </div>
                    </div>
                    {index < allItems.length - 1 && <Separator />}
                  </div>
                );
              })
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
