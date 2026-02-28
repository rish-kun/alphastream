"use client";

import Link from "next/link";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import type { Stock } from "@/types/stock";

interface StockCardProps {
  stock: Stock;
  sentimentScore?: number | null;
}

function getSentimentColor(score: number | null | undefined): string {
  if (score == null) return "bg-gray-400";
  if (score > 0.1) return "bg-green-500";
  if (score < -0.1) return "bg-red-500";
  return "bg-gray-400";
}

export function StockCard({ stock, sentimentScore }: StockCardProps) {
  const hasPrice = stock.last_price != null;

  return (
    <Link href={`/stocks/${stock.ticker}`}>
      <Card className="transition-all hover:bg-muted/50 hover:shadow-md cursor-pointer h-full">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <div className="flex items-center gap-2">
            <span
              className={`h-2 w-2 rounded-full ${getSentimentColor(sentimentScore)}`}
              title={
                sentimentScore != null
                  ? `Sentiment: ${sentimentScore.toFixed(2)}`
                  : "No sentiment data"
              }
            />
            <CardTitle className="text-base font-bold">
              {stock.ticker}
            </CardTitle>
          </div>
          <Badge variant="outline" className="text-xs">
            {stock.sector || "N/A"}
          </Badge>
        </CardHeader>
        <CardContent>
          <p className="mb-2 text-sm text-muted-foreground line-clamp-1">
            {stock.company_name}
          </p>
          <div className="flex items-center justify-between">
            {hasPrice ? (
              <span className="text-lg font-semibold">
                &#8377;
                {stock.last_price!.toLocaleString("en-IN", {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </span>
            ) : (
              <span className="text-sm text-muted-foreground">
                Price unavailable
              </span>
            )}
            {sentimentScore != null && (
              <span
                className={`flex items-center gap-1 text-sm font-medium ${
                  sentimentScore > 0
                    ? "text-green-600"
                    : sentimentScore < 0
                      ? "text-red-600"
                      : "text-muted-foreground"
                }`}
              >
                {sentimentScore > 0 ? (
                  <TrendingUp className="h-4 w-4" />
                ) : sentimentScore < 0 ? (
                  <TrendingDown className="h-4 w-4" />
                ) : (
                  <Minus className="h-4 w-4" />
                )}
                {sentimentScore > 0 ? "+" : ""}
                {sentimentScore.toFixed(2)}
              </span>
            )}
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}

// Compact card for use in search results and lists
export function StockCardCompact({ stock }: { stock: Stock }) {
  return (
    <Link
      href={`/stocks/${stock.ticker}`}
      className="flex items-center justify-between rounded-lg border p-3 transition-colors hover:bg-muted/50"
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
          <Badge variant="outline" className="text-xs hidden sm:inline-flex">
            {stock.sector}
          </Badge>
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
    </Link>
  );
}
