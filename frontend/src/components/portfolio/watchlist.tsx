"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Plus,
  Eye,
  TrendingUp,
  TrendingDown,
  X,
  Loader2,
  AlertCircle,
} from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";
import {
  getPortfolios,
  createPortfolio,
  addStockToPortfolio,
  removeStockFromPortfolio,
  getPortfolioAlpha,
} from "@/lib/api";
import { StockSearch } from "@/components/stocks/stock-search";
import type { Portfolio, PortfolioAlphaResponse } from "@/types/api";
import type { Stock } from "@/types/stock";

const WATCHLIST_NAME = "__watchlist__";

export function Watchlist() {
  const queryClient = useQueryClient();
  const [addOpen, setAddOpen] = useState(false);

  // Fetch portfolios and find the watchlist
  const { data: portfoliosData, isLoading } = useQuery({
    queryKey: ["portfolios"],
    queryFn: getPortfolios,
  });

  const portfolios = portfoliosData?.portfolios ?? [];
  const watchlist = portfolios.find((p) => p.name === WATCHLIST_NAME);

  // Fetch alpha metrics for watchlist stocks
  const { data: alphaData } = useQuery({
    queryKey: ["portfolio", watchlist?.id, "alpha"],
    queryFn: () => getPortfolioAlpha(watchlist!.id),
    enabled: !!watchlist?.id && watchlist.stocks.length > 0,
  });

  const alphaByTicker: Record<string, { signal: string; score: number }> = {};
  if (alphaData?.metrics) {
    for (const m of alphaData.metrics) {
      alphaByTicker[m.ticker] = {
        signal: m.signal,
        score: m.composite_score,
      };
    }
  }

  // Create watchlist if it doesn't exist
  const createWatchlistMutation = useMutation({
    mutationFn: () =>
      createPortfolio({
        name: WATCHLIST_NAME,
        description: "Quick watchlist",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["portfolios"] });
    },
  });

  // Add stock
  const addStockMutation = useMutation({
    mutationFn: async (stock: Stock) => {
      let wlId = watchlist?.id;
      if (!wlId) {
        const created = await createPortfolio({
          name: WATCHLIST_NAME,
          description: "Quick watchlist",
        });
        wlId = created.id;
      }
      return addStockToPortfolio(wlId, stock.ticker);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["portfolios"] });
      setAddOpen(false);
      toast.success("Stock added to watchlist");
    },
    onError: (err) => {
      toast.error(
        `Failed to add stock: ${err instanceof Error ? err.message : "Unknown error"}`
      );
    },
  });

  // Remove stock
  const removeStockMutation = useMutation({
    mutationFn: (ticker: string) => {
      if (!watchlist) throw new Error("Watchlist not found");
      return removeStockFromPortfolio(watchlist.id, ticker);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["portfolios"] });
      toast.success("Stock removed from watchlist");
    },
    onError: (err) => {
      toast.error(
        `Failed to remove stock: ${err instanceof Error ? err.message : "Unknown error"}`
      );
    },
  });

  const watchlistStocks = watchlist?.stocks ?? [];

  return (
    <>
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div className="flex items-center gap-2">
            <Eye className="h-5 w-5 text-muted-foreground" />
            <div>
              <CardTitle className="text-base">Watchlist</CardTitle>
              <CardDescription className="text-xs">
                Quick-track stocks with real-time sentiment
              </CardDescription>
            </div>
          </div>
          <Button
            size="sm"
            variant="outline"
            className="gap-1.5 h-8"
            onClick={() => setAddOpen(true)}
          >
            <Plus className="h-3.5 w-3.5" />
            Add
          </Button>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 4 }).map((_, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between rounded-lg p-3"
                >
                  <div className="space-y-1">
                    <Skeleton className="h-4 w-20" />
                    <Skeleton className="h-3 w-32" />
                  </div>
                  <div className="flex items-center gap-3">
                    <Skeleton className="h-4 w-16" />
                    <Skeleton className="h-5 w-14 rounded-full" />
                  </div>
                </div>
              ))}
            </div>
          ) : watchlistStocks.length === 0 ? (
            <div className="flex flex-col items-center justify-center rounded-lg border border-dashed py-8 text-center">
              <Eye className="mb-2 h-8 w-8 text-muted-foreground/50" />
              <p className="text-sm text-muted-foreground">
                Your watchlist is empty
              </p>
              <p className="text-xs text-muted-foreground/70 mt-1">
                Add stocks to track their sentiment in real-time
              </p>
              <Button
                size="sm"
                variant="outline"
                className="mt-3 gap-1.5"
                onClick={() => setAddOpen(true)}
              >
                <Plus className="h-3.5 w-3.5" />
                Add Stock
              </Button>
            </div>
          ) : (
            <ScrollArea className="max-h-[400px]">
              <div className="space-y-1">
                {watchlistStocks.map((stock, index) => {
                  const alpha = alphaByTicker[stock.ticker];
                  const isBullish = alpha
                    ? alpha.signal.includes("buy")
                    : undefined;
                  const isBearish = alpha
                    ? alpha.signal.includes("sell")
                    : undefined;

                  return (
                    <div key={stock.ticker}>
                      <div className="flex items-center justify-between rounded-lg p-3 transition-colors hover:bg-muted/50 group">
                        <Link
                          href={`/stocks/${stock.ticker}`}
                          className="flex-1 min-w-0"
                        >
                          <p className="text-sm font-semibold">
                            {stock.ticker}
                          </p>
                          <p className="text-xs text-muted-foreground truncate">
                            {stock.company_name}
                          </p>
                        </Link>
                        <div className="flex items-center gap-2 shrink-0">
                          {alpha && (
                            <div className="text-right">
                              <p
                                className={`text-xs font-medium tabular-nums ${
                                  alpha.score > 0
                                    ? "text-green-600"
                                    : alpha.score < 0
                                      ? "text-red-600"
                                      : "text-muted-foreground"
                                }`}
                              >
                                {alpha.score > 0 ? "+" : ""}
                                {alpha.score.toFixed(2)}
                              </p>
                            </div>
                          )}
                          {alpha && (
                            <Badge
                              variant="outline"
                              className={`text-xs ${
                                isBullish
                                  ? "border-green-500/20 bg-green-500/10 text-green-600"
                                  : isBearish
                                    ? "border-red-500/20 bg-red-500/10 text-red-600"
                                    : "border-gray-500/20 bg-gray-500/10 text-gray-600"
                              }`}
                            >
                              {isBullish
                                ? "Bullish"
                                : isBearish
                                  ? "Bearish"
                                  : "Neutral"}
                            </Badge>
                          )}
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-7 w-7 opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-destructive"
                            onClick={(e) => {
                              e.preventDefault();
                              removeStockMutation.mutate(stock.ticker);
                            }}
                            disabled={removeStockMutation.isPending}
                          >
                            <X className="h-3.5 w-3.5" />
                          </Button>
                        </div>
                      </div>
                      {index < watchlistStocks.length - 1 && <Separator />}
                    </div>
                  );
                })}
              </div>
            </ScrollArea>
          )}
        </CardContent>
      </Card>

      {/* Add Stock Dialog */}
      <Dialog open={addOpen} onOpenChange={setAddOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Add to Watchlist</DialogTitle>
            <DialogDescription>
              Search for a stock to add to your watchlist
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <StockSearch
              onSelect={(stock) => addStockMutation.mutate(stock)}
              compact
            />
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
