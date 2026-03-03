"use client";

import { Loader2, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

interface ReanalyzingBadgeProps {
  status?: "pending" | "started" | "analyzing" | "completed" | "failed" | "not_found";
  className?: string;
  showText?: boolean;
}

export function ReanalyzingBadge({
  status = "analyzing",
  className,
  showText = true,
}: ReanalyzingBadgeProps) {
  const isActive = status === "pending" || status === "started" || status === "analyzing";
  const isCompleted = status === "completed";
  const isFailed = status === "failed";

  if (!isActive && !isCompleted && !isFailed) {
    return null;
  }

  return (
    <div
      className={cn(
        "inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium transition-all duration-300",
        isActive && "border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-400",
        isCompleted && "border-green-200 bg-green-50 text-green-700 dark:border-green-800 dark:bg-green-950/30 dark:text-green-400",
        isFailed && "border-red-200 bg-red-50 text-red-700 dark:border-red-800 dark:bg-red-950/30 dark:text-red-400",
        className
      )}
    >
      {isActive && (
        <>
          {/* Animated pulse dot */}
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-amber-400 opacity-75 dark:bg-amber-500" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-amber-500 dark:bg-amber-400" />
          </span>
          {showText && (
            <span className="flex items-center gap-1">
              <Sparkles className="h-3 w-3 animate-pulse" />
              Analyzing again
              <span className="animate-pulse">...</span>
            </span>
          )}
        </>
      )}
      
      {isCompleted && (
        <>
          <span className="relative flex h-2 w-2">
            <span className="relative inline-flex h-2 w-2 rounded-full bg-green-500 dark:bg-green-400" />
          </span>
          {showText && <span>Analysis complete</span>}
        </>
      )}
      
      {isFailed && (
        <>
          <span className="relative flex h-2 w-2">
            <span className="relative inline-flex h-2 w-2 rounded-full bg-red-500 dark:bg-red-400" />
          </span>
          {showText && <span>Analysis failed</span>}
        </>
      )}
    </div>
  );
}

interface ReanalyzingOverlayProps {
  isReanalyzing: boolean;
  children: React.ReactNode;
  className?: string;
}

export function ReanalyzingOverlay({
  isReanalyzing,
  children,
  className,
}: ReanalyzingOverlayProps) {
  return (
    <div className={cn("relative", className)}>
      {children}
      {isReanalyzing && (
        <div className="absolute inset-0 flex items-center justify-center rounded-lg bg-background/50 backdrop-blur-[1px] transition-all">
          <div className="flex items-center gap-2 rounded-full border border-amber-200 bg-amber-50 px-4 py-2 text-sm font-medium text-amber-700 shadow-sm dark:border-amber-800 dark:bg-amber-950/50 dark:text-amber-400">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>Reanalyzing sentiment...</span>
          </div>
        </div>
      )}
    </div>
  );
}
