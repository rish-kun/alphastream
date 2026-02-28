"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { PortfolioManager } from "@/components/portfolio/portfolio-manager";
import { Watchlist } from "@/components/portfolio/watchlist";
import { useAuth } from "@/providers/auth-provider";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Activity,
  Newspaper,
  Loader2,
  TrendingUp,
  TrendingDown,
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import {
  getPortfolios,
  getPortfolioAlpha,
  getPortfolioNews,
} from "@/lib/api";
import { ResearchToggle } from "@/components/research/research-toggle";
import type { PortfolioAlphaResponse, PortfolioNewsResponse } from "@/types/api";

export default function PortfolioPage() {
  const { user, isLoading: isAuthLoading } = useAuth();
  const router = useRouter();
  const [selectedPortfolioId, setSelectedPortfolioId] = useState<string | null>(
    null
  );

  // Redirect if not authenticated
  useEffect(() => {
    if (!isAuthLoading && !user) {
      router.push("/login");
    }
  }, [user, isAuthLoading, router]);

  // Get portfolios for the selector
  const { data: portfoliosData } = useQuery({
    queryKey: ["portfolios"],
    queryFn: getPortfolios,
    enabled: !!user,
  });

  const portfolios = (portfoliosData?.portfolios ?? []).filter(
    (p) => p.name !== "__watchlist__"
  );

  // Auto-select the first portfolio
  useEffect(() => {
    if (!selectedPortfolioId && portfolios.length > 0) {
      setSelectedPortfolioId(portfolios[0].id);
    }
  }, [portfolios, selectedPortfolioId]);

  // Fetch alpha for selected portfolio
  const { data: alphaData, isLoading: isAlphaLoading } = useQuery({
    queryKey: ["portfolio", selectedPortfolioId, "alpha"],
    queryFn: () => getPortfolioAlpha(selectedPortfolioId!),
    enabled: !!selectedPortfolioId,
  });

  // Fetch news for selected portfolio
  const { data: newsData, isLoading: isNewsLoading } = useQuery({
    queryKey: ["portfolio", selectedPortfolioId, "news"],
    queryFn: () => getPortfolioNews(selectedPortfolioId!),
    enabled: !!selectedPortfolioId,
  });

  // Auth loading state
  if (isAuthLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!user) {
    return null; // Will redirect
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Portfolio</h1>
        <p className="text-muted-foreground">
          Manage your portfolios and track watchlist sentiment
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left side: Portfolio Manager and Watchlist */}
        <div className="lg:col-span-2 space-y-6">
          <PortfolioManager />
          <Watchlist />
        </div>

        {/* Right side: Portfolio Alpha & News */}
        <div className="space-y-6">
          {/* Portfolio Selector */}
          {portfolios.length > 0 && (
            <div className="space-y-3">
              <Select
                value={selectedPortfolioId ?? undefined}
                onValueChange={setSelectedPortfolioId}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select portfolio" />
                </SelectTrigger>
                <SelectContent>
                  {portfolios.map((p) => (
                    <SelectItem key={p.id} value={p.id}>
                      {p.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

          {/* Extensive Research for selected portfolio */}
          {selectedPortfolioId && (
            <ResearchToggle
              type="portfolio"
              portfolioId={selectedPortfolioId}
            />
          )}

          {/* Portfolio Alpha Metrics */}
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <Activity className="h-4 w-4 text-muted-foreground" />
                <CardTitle className="text-base">Portfolio Alpha</CardTitle>
              </div>
              <CardDescription className="text-xs">
                Alpha signals for portfolio stocks
              </CardDescription>
            </CardHeader>
            <CardContent>
              {!selectedPortfolioId ? (
                <p className="text-sm text-muted-foreground text-center py-4">
                  Select a portfolio to view alpha metrics
                </p>
              ) : isAlphaLoading ? (
                <div className="space-y-3">
                  {Array.from({ length: 4 }).map((_, i) => (
                    <div
                      key={i}
                      className="flex items-center justify-between"
                    >
                      <Skeleton className="h-4 w-20" />
                      <Skeleton className="h-4 w-16" />
                    </div>
                  ))}
                </div>
              ) : alphaData && alphaData.metrics.length > 0 ? (
                <div className="space-y-1">
                  {alphaData.metrics.map((metric, index) => {
                    const isBullish = metric.signal.includes("buy");
                    const isBearish = metric.signal.includes("sell");
                    return (
                      <div key={metric.ticker}>
                        <div className="flex items-center justify-between rounded-lg p-2 transition-colors hover:bg-muted/50">
                          <div>
                            <p className="text-sm font-semibold">
                              {metric.ticker}
                            </p>
                            <p className="text-xs text-muted-foreground truncate max-w-[120px]">
                              {metric.company_name}
                            </p>
                          </div>
                          <div className="flex items-center gap-2">
                            <span
                              className={`text-xs font-medium tabular-nums ${
                                metric.composite_score > 0
                                  ? "text-green-600"
                                  : metric.composite_score < 0
                                    ? "text-red-600"
                                    : "text-muted-foreground"
                              }`}
                            >
                              {metric.composite_score > 0 ? "+" : ""}
                              {metric.composite_score.toFixed(2)}
                            </span>
                            <Badge
                              variant="outline"
                              className={`text-xs ${
                                isBullish
                                  ? "border-green-500/20 bg-green-500/10 text-green-600"
                                  : isBearish
                                    ? "border-red-500/20 bg-red-500/10 text-red-600"
                                    : ""
                              }`}
                            >
                              {isBullish ? (
                                <TrendingUp className="mr-1 h-3 w-3" />
                              ) : isBearish ? (
                                <TrendingDown className="mr-1 h-3 w-3" />
                              ) : null}
                              {metric.signal.replace("_", " ")}
                            </Badge>
                          </div>
                        </div>
                        {index < alphaData.metrics.length - 1 && (
                          <Separator />
                        )}
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground text-center py-4">
                  No alpha data available
                </p>
              )}
            </CardContent>
          </Card>

          {/* Portfolio News */}
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <Newspaper className="h-4 w-4 text-muted-foreground" />
                <CardTitle className="text-base">Portfolio News</CardTitle>
              </div>
              <CardDescription className="text-xs">
                Recent news for portfolio stocks
              </CardDescription>
            </CardHeader>
            <CardContent>
              {!selectedPortfolioId ? (
                <p className="text-sm text-muted-foreground text-center py-4">
                  Select a portfolio to view news
                </p>
              ) : isNewsLoading ? (
                <div className="space-y-3">
                  {Array.from({ length: 4 }).map((_, i) => (
                    <div key={i} className="space-y-1.5">
                      <Skeleton className="h-4 w-full" />
                      <Skeleton className="h-3 w-3/4" />
                      <Skeleton className="h-3 w-1/2" />
                    </div>
                  ))}
                </div>
              ) : newsData && newsData.items.length > 0 ? (
                <div className="space-y-1">
                  {newsData.items.slice(0, 10).map((article, index) => (
                    <div key={article.id}>
                      <div className="rounded-lg p-2 transition-colors hover:bg-muted/50">
                        <p className="text-sm font-medium leading-snug line-clamp-2">
                          {article.title}
                        </p>
                        <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
                          <Badge variant="outline" className="text-xs h-5">
                            {article.ticker}
                          </Badge>
                          <span>{article.source}</span>
                          <span className="text-muted-foreground/40">|</span>
                          <span>
                            {formatDistanceToNow(
                              new Date(article.published_at),
                              { addSuffix: true }
                            )}
                          </span>
                          {article.sentiment_score != null && (
                            <span
                              className={`font-medium ${
                                article.sentiment_score > 0
                                  ? "text-green-600"
                                  : article.sentiment_score < 0
                                    ? "text-red-600"
                                    : ""
                              }`}
                            >
                              {article.sentiment_score > 0 ? "+" : ""}
                              {article.sentiment_score.toFixed(2)}
                            </span>
                          )}
                        </div>
                      </div>
                      {index <
                        Math.min(newsData.items.length, 10) - 1 && (
                        <Separator />
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground text-center py-4">
                  No news available
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
