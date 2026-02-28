"use client";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface SentimentBadgeProps {
  score: number;
  size?: "sm" | "md" | "lg";
  showValue?: boolean;
  className?: string;
}

function getSentimentLabel(score: number): string {
  if (score >= 0.5) return "Very Bullish";
  if (score >= 0.2) return "Bullish";
  if (score > -0.2) return "Neutral";
  if (score > -0.5) return "Bearish";
  return "Very Bearish";
}

function getSentimentColor(score: number): string {
  if (score >= 0.5) return "bg-green-600 text-white hover:bg-green-600";
  if (score >= 0.2) return "bg-green-500/10 text-green-600 border-green-500/20";
  if (score > -0.2)
    return "bg-yellow-500/10 text-yellow-600 border-yellow-500/20";
  if (score > -0.5) return "bg-red-500/10 text-red-600 border-red-500/20";
  return "bg-red-600 text-white hover:bg-red-600";
}

function formatScore(score: number): string {
  const formatted = score.toFixed(2);
  return score > 0 ? `+${formatted}` : formatted;
}

const sizeClasses = {
  sm: "text-[10px] px-1.5 py-0",
  md: "text-xs px-2.5 py-0.5",
  lg: "text-sm px-3 py-1",
} as const;

export function SentimentBadge({
  score,
  size = "md",
  showValue = true,
  className,
}: SentimentBadgeProps) {
  const label = getSentimentLabel(score);
  const colorClass = getSentimentColor(score);

  return (
    <Badge
      variant="outline"
      className={cn(colorClass, sizeClasses[size], className)}
    >
      {label}
      {showValue && (
        <span className="ml-1 font-mono">({formatScore(score)})</span>
      )}
    </Badge>
  );
}
