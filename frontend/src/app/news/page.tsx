"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { useInfiniteQuery, useQuery } from "@tanstack/react-query";
import { NewsCard } from "@/components/news/news-card";
import { SentimentBadge } from "@/components/news/sentiment-badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  TrendingUp,
  Newspaper,
  Search,
  Loader2,
  Filter,
  X,
} from "lucide-react";
import { getNewsFeed, getTrendingNews } from "@/lib/api";
import { ResearchToggle } from "@/components/research/research-toggle";
import type { NewsFeedParams } from "@/types/news";

const NEWS_SOURCES = [
  { value: "all", label: "All Sources" },
  { value: "Economic Times", label: "Economic Times" },
  { value: "Moneycontrol", label: "Moneycontrol" },
  { value: "LiveMint", label: "LiveMint" },
  { value: "Business Standard", label: "Business Standard" },
  { value: "NDTV Profit", label: "NDTV Profit" },
  { value: "Reuters", label: "Reuters" },
  { value: "Bloomberg", label: "Bloomberg" },
];

const PAGE_SIZE = 20;

export default function NewsPage() {
  const [source, setSource] = useState("all");
  const [ticker, setTicker] = useState("");
  const [tickerInput, setTickerInput] = useState("");
  const observerRef = useRef<IntersectionObserver | null>(null);

  const filters: NewsFeedParams = {
    size: PAGE_SIZE,
    ...(source !== "all" && { source }),
    ...(ticker && { ticker }),
  };

  // Trending news query
  const {
    data: trendingData,
    isLoading: trendingLoading,
  } = useQuery({
    queryKey: ["trending-news"],
    queryFn: getTrendingNews,
    staleTime: 5 * 60 * 1000,
  });

  // Infinite scroll news feed
  const {
    data,
    isLoading,
    isFetchingNextPage,
    fetchNextPage,
    hasNextPage,
  } = useInfiniteQuery({
    queryKey: ["news", filters],
    queryFn: ({ pageParam = 1 }) =>
      getNewsFeed({ page: pageParam, ...filters }),
    getNextPageParam: (lastPage) =>
      lastPage.page < Math.ceil(lastPage.total / lastPage.size)
        ? lastPage.page + 1
        : undefined,
    initialPageParam: 1,
  });

  // Intersection observer for infinite scroll
  const lastItemRef = useCallback(
    (node: HTMLDivElement | null) => {
      if (isFetchingNextPage) return;
      if (observerRef.current) observerRef.current.disconnect();

      observerRef.current = new IntersectionObserver(
        (entries) => {
          if (entries[0]?.isIntersecting && hasNextPage) {
            fetchNextPage();
          }
        },
        { threshold: 0.1 }
      );

      if (node) observerRef.current.observe(node);
    },
    [isFetchingNextPage, hasNextPage, fetchNextPage]
  );

  // Cleanup observer on unmount
  useEffect(() => {
    return () => {
      if (observerRef.current) observerRef.current.disconnect();
    };
  }, []);

  const allArticles = data?.pages.flatMap((page) => page.items) ?? [];
  const totalArticles = data?.pages[0]?.total ?? 0;

  const handleTickerSearch = () => {
    setTicker(tickerInput.trim().toUpperCase());
  };

  const clearFilters = () => {
    setSource("all");
    setTicker("");
    setTickerInput("");
  };

  const hasActiveFilters = source !== "all" || ticker !== "";

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">News Feed</h1>
        <p className="text-muted-foreground">
          Latest financial news with AI-powered sentiment analysis
        </p>
      </div>

      {/* Trending News Section */}
      {(trendingLoading || (trendingData?.articles?.length ?? 0) > 0) && (
        <div>
          <div className="mb-3 flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-primary" />
            <h2 className="text-lg font-semibold">Trending</h2>
          </div>
          <ScrollArea className="w-full whitespace-nowrap">
            <div className="flex gap-3 pb-3">
              {trendingLoading
                ? Array.from({ length: 4 }).map((_, i) => (
                    <TrendingCardSkeleton key={i} />
                  ))
                : trendingData?.articles?.map((article) => (
                    <div key={article.id} className="w-[280px] shrink-0">
                      <NewsCard article={article} variant="trending" />
                    </div>
                  ))}
            </div>
            <ScrollBar orientation="horizontal" />
          </ScrollArea>
        </div>
      )}

      {/* Filter Bar */}
      <Card>
        <CardContent className="py-3">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
              <Filter className="h-4 w-4" />
              Filters
            </div>

            {/* Source Filter */}
            <Select value={source} onValueChange={setSource}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Source" />
              </SelectTrigger>
              <SelectContent>
                {NEWS_SOURCES.map((s) => (
                  <SelectItem key={s.value} value={s.value}>
                    {s.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Ticker Search */}
            <div className="flex items-center gap-1">
              <Input
                placeholder="Ticker (e.g. RELIANCE)"
                value={tickerInput}
                onChange={(e) => setTickerInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleTickerSearch()}
                className="w-[200px]"
              />
              <Button
                size="icon"
                variant="ghost"
                onClick={handleTickerSearch}
              >
                <Search className="h-4 w-4" />
              </Button>
            </div>

            {/* Active filter badges & clear */}
            {hasActiveFilters && (
              <>
                <div className="flex flex-wrap gap-1.5">
                  {source !== "all" && (
                    <Badge
                      variant="secondary"
                      className="gap-1 cursor-pointer"
                      onClick={() => setSource("all")}
                    >
                      {source}
                      <X className="h-3 w-3" />
                    </Badge>
                  )}
                  {ticker && (
                    <Badge
                      variant="secondary"
                      className="gap-1 cursor-pointer font-mono"
                      onClick={() => {
                        setTicker("");
                        setTickerInput("");
                      }}
                    >
                      {ticker}
                      <X className="h-3 w-3" />
                    </Badge>
                  )}
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearFilters}
                  className="text-muted-foreground"
                >
                  Clear all
                </Button>
              </>
            )}

            {/* Result count */}
            {!isLoading && (
              <span className="ml-auto text-sm text-muted-foreground">
                {totalArticles} article{totalArticles !== 1 ? "s" : ""}
              </span>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Extensive Research for filtered topic */}
      {ticker && (
        <ResearchToggle type="stock" ticker={ticker} compact />
      )}

      {/* News Feed */}
      <div className="space-y-3">
        {isLoading ? (
          Array.from({ length: 5 }).map((_, i) => (
            <NewsCardSkeleton key={i} />
          ))
        ) : allArticles.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <Newspaper className="h-12 w-12 text-muted-foreground" />
              <h3 className="mt-4 text-lg font-semibold">No articles found</h3>
              <p className="mt-1 text-sm text-muted-foreground">
                {hasActiveFilters
                  ? "Try adjusting your filters"
                  : "Check back later for new articles"}
              </p>
              {hasActiveFilters && (
                <Button
                  variant="outline"
                  size="sm"
                  className="mt-3"
                  onClick={clearFilters}
                >
                  Clear filters
                </Button>
              )}
            </CardContent>
          </Card>
        ) : (
          <>
            {allArticles.map((article, index) => {
              const isLast = index === allArticles.length - 1;
              return (
                <div key={article.id} ref={isLast ? lastItemRef : undefined}>
                  <NewsCard article={article} />
                </div>
              );
            })}

            {/* Loading more indicator */}
            {isFetchingNextPage && (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                <span className="ml-2 text-sm text-muted-foreground">
                  Loading more articles...
                </span>
              </div>
            )}

            {/* Manual load more button as fallback */}
            {hasNextPage && !isFetchingNextPage && (
              <div className="flex justify-center pt-2">
                <Button
                  variant="outline"
                  onClick={() => fetchNextPage()}
                >
                  Load More
                </Button>
              </div>
            )}

            {/* End of feed */}
            {!hasNextPage && allArticles.length > 0 && (
              <p className="py-4 text-center text-sm text-muted-foreground">
                You&apos;ve reached the end of the news feed
              </p>
            )}
          </>
        )}
      </div>
    </div>
  );
}

function NewsCardSkeleton() {
  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 space-y-2">
            <Skeleton className="h-5 w-3/4" />
            <div className="flex items-center gap-2">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-4 w-16" />
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Skeleton className="h-6 w-16 rounded-md" />
            <Skeleton className="h-6 w-24 rounded-md" />
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <Skeleton className="h-4 w-full" />
        <Skeleton className="mt-2 h-4 w-5/6" />
        <div className="mt-3 flex gap-1.5">
          <Skeleton className="h-5 w-16 rounded-md" />
          <Skeleton className="h-5 w-14 rounded-md" />
        </div>
      </CardContent>
    </Card>
  );
}

function TrendingCardSkeleton() {
  return (
    <Card className="h-full min-w-[280px]">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between gap-2">
          <Skeleton className="h-5 w-20 rounded-md" />
          <Skeleton className="h-5 w-16 rounded-md" />
        </div>
        <Skeleton className="mt-2 h-4 w-full" />
        <Skeleton className="h-4 w-3/4" />
      </CardHeader>
      <CardContent className="pt-0">
        <Skeleton className="h-3 w-16" />
      </CardContent>
    </Card>
  );
}
