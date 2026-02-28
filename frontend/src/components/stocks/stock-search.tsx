"use client";

import { useState, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search, Loader2, X } from "lucide-react";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { StockCardCompact } from "@/components/stocks/stock-card";
import { searchStocks, getSectors } from "@/lib/api";
import { useDebounce } from "@/hooks/use-debounce";
import type { Stock } from "@/types/stock";

interface StockSearchProps {
  onSelect?: (stock: Stock) => void;
  compact?: boolean;
}

export function StockSearch({ onSelect, compact = false }: StockSearchProps) {
  const [query, setQuery] = useState("");
  const [sectorFilter, setSectorFilter] = useState("all");
  const debouncedQuery = useDebounce(query, 300);

  const {
    data: searchResult,
    isLoading: isSearching,
    isFetching,
  } = useQuery({
    queryKey: ["stocks", "search", debouncedQuery],
    queryFn: () => searchStocks(debouncedQuery, 20),
    enabled: debouncedQuery.length >= 1,
    staleTime: 30 * 1000,
  });

  const { data: sectorsData } = useQuery({
    queryKey: ["sectors"],
    queryFn: getSectors,
    staleTime: 5 * 60 * 1000,
  });

  const sectors = sectorsData?.sectors ?? [];

  const filteredStocks =
    sectorFilter === "all"
      ? searchResult?.stocks ?? []
      : (searchResult?.stocks ?? []).filter(
          (s) => s.sector.toLowerCase() === sectorFilter.toLowerCase()
        );

  const handleClear = useCallback(() => {
    setQuery("");
    setSectorFilter("all");
  }, []);

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search by ticker or company name..."
            className="pl-9 pr-9"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          {query && (
            <Button
              variant="ghost"
              size="icon"
              className="absolute right-1 top-1 h-8 w-8"
              onClick={handleClear}
            >
              <X className="h-3 w-3" />
            </Button>
          )}
          {isFetching && (
            <Loader2 className="absolute right-10 top-3 h-4 w-4 animate-spin text-muted-foreground" />
          )}
        </div>
        <Select value={sectorFilter} onValueChange={setSectorFilter}>
          <SelectTrigger className="w-full sm:w-[200px]">
            <SelectValue placeholder="Filter by sector" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Sectors</SelectItem>
            {sectors.map((sector) => (
              <SelectItem key={sector.name} value={sector.name.toLowerCase()}>
                {sector.name} ({sector.stock_count})
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Results section */}
      {debouncedQuery.length === 0 && !compact && (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed py-12 text-center">
          <Search className="mb-3 h-10 w-10 text-muted-foreground/50" />
          <p className="text-sm font-medium text-muted-foreground">
            Search for stocks by name or ticker
          </p>
          <p className="text-xs text-muted-foreground/70 mt-1">
            Try &quot;Reliance&quot;, &quot;TCS&quot;, or &quot;HDFC&quot;
          </p>
        </div>
      )}

      {isSearching && debouncedQuery.length >= 1 && (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <div
              key={i}
              className="flex items-center justify-between rounded-lg border p-3"
            >
              <div className="flex items-center gap-3">
                <Skeleton className="h-10 w-10 rounded-lg" />
                <div className="space-y-1">
                  <Skeleton className="h-4 w-20" />
                  <Skeleton className="h-3 w-32" />
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Skeleton className="h-5 w-16 rounded-full" />
                <Skeleton className="h-4 w-20" />
              </div>
            </div>
          ))}
        </div>
      )}

      {!isSearching && filteredStocks.length > 0 && (
        <div className="space-y-1">
          {filteredStocks.map((stock) =>
            onSelect ? (
              <button
                key={stock.id}
                type="button"
                className="flex w-full items-center justify-between rounded-lg border p-3 text-left transition-colors hover:bg-muted/50"
                onClick={() => onSelect(stock)}
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 font-bold text-primary text-xs">
                    {stock.ticker.slice(0, 3)}
                  </div>
                  <div>
                    <p className="text-sm font-semibold">{stock.ticker}</p>
                    <p className="text-xs text-muted-foreground line-clamp-1">
                      {stock.company_name}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {stock.sector && (
                    <span className="rounded-full border px-2 py-0.5 text-xs hidden sm:inline">
                      {stock.sector}
                    </span>
                  )}
                  {stock.last_price != null && (
                    <span className="text-sm font-medium tabular-nums">
                      &#8377;
                      {stock.last_price.toLocaleString("en-IN", {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}
                    </span>
                  )}
                </div>
              </button>
            ) : (
              <StockCardCompact key={stock.id} stock={stock} />
            )
          )}
        </div>
      )}

      {!isSearching &&
        debouncedQuery.length >= 1 &&
        filteredStocks.length === 0 && (
          <div className="flex flex-col items-center justify-center rounded-lg border border-dashed py-8 text-center">
            <p className="text-sm text-muted-foreground">
              No stocks found for &quot;{debouncedQuery}&quot;
              {sectorFilter !== "all" && ` in ${sectorFilter}`}
            </p>
            <p className="text-xs text-muted-foreground/70 mt-1">
              Try a different search term or clear the sector filter
            </p>
          </div>
        )}
    </div>
  );
}
