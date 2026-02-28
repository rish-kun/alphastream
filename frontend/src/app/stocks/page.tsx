"use client";

import { useQuery } from "@tanstack/react-query";
import { StockSearch } from "@/components/stocks/stock-search";
import { StockCard } from "@/components/stocks/stock-card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Building2, TrendingUp, BarChart3 } from "lucide-react";
import Link from "next/link";
import { getSectors, searchStocks } from "@/lib/api";

export default function StocksPage() {
  const { data: sectorsData, isLoading: isSectorsLoading } = useQuery({
    queryKey: ["sectors"],
    queryFn: getSectors,
    staleTime: 5 * 60 * 1000,
  });

  // Fetch some popular stocks (empty query returns popular/all)
  const { data: popularData, isLoading: isPopularLoading } = useQuery({
    queryKey: ["stocks", "popular"],
    queryFn: () => searchStocks("", 6),
    staleTime: 2 * 60 * 1000,
  });

  const sectors = sectorsData?.sectors ?? [];
  const popularStocks = popularData?.stocks ?? [];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Stocks</h1>
        <p className="text-muted-foreground">
          Search and analyze stocks listed on Indian exchanges
        </p>
      </div>

      <StockSearch />

      {/* Sectors Grid */}
      <section>
        <div className="flex items-center gap-2 mb-4">
          <Building2 className="h-5 w-5 text-muted-foreground" />
          <h2 className="text-xl font-semibold">Sectors</h2>
        </div>
        {isSectorsLoading ? (
          <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
            {Array.from({ length: 8 }).map((_, i) => (
              <Card key={i}>
                <CardContent className="p-4">
                  <Skeleton className="h-5 w-24 mb-2" />
                  <Skeleton className="h-4 w-16" />
                </CardContent>
              </Card>
            ))}
          </div>
        ) : sectors.length > 0 ? (
          <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
            {sectors.map((sector) => (
              <Card
                key={sector.name}
                className="transition-colors hover:bg-muted/50 cursor-default"
              >
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-semibold">{sector.name}</p>
                    <Badge variant="secondary" className="text-xs">
                      {sector.stock_count}
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    {sector.stock_count} stock{sector.stock_count !== 1 ? "s" : ""}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-8 text-center">
              <Building2 className="mb-2 h-8 w-8 text-muted-foreground/50" />
              <p className="text-sm text-muted-foreground">
                No sector data available
              </p>
            </CardContent>
          </Card>
        )}
      </section>

      {/* Popular Stocks */}
      <section>
        <div className="flex items-center gap-2 mb-4">
          <TrendingUp className="h-5 w-5 text-muted-foreground" />
          <h2 className="text-xl font-semibold">Popular Stocks</h2>
        </div>
        {isPopularLoading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <Card key={i}>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <Skeleton className="h-5 w-20" />
                  <Skeleton className="h-5 w-16 rounded-full" />
                </CardHeader>
                <CardContent>
                  <Skeleton className="h-4 w-40 mb-3" />
                  <Skeleton className="h-6 w-24" />
                </CardContent>
              </Card>
            ))}
          </div>
        ) : popularStocks.length > 0 ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {popularStocks.map((stock) => (
              <StockCard key={stock.id} stock={stock} />
            ))}
          </div>
        ) : (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-8 text-center">
              <BarChart3 className="mb-2 h-8 w-8 text-muted-foreground/50" />
              <p className="text-sm text-muted-foreground">
                No stock data available yet
              </p>
            </CardContent>
          </Card>
        )}
      </section>
    </div>
  );
}
