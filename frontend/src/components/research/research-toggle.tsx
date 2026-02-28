"use client";

import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import {
  Loader2,
  Search,
  CheckCircle2,
  XCircle,
  Sparkles,
} from "lucide-react";
import {
  researchStock,
  researchPortfolio,
  researchTopic,
  getResearchStatus,
} from "@/lib/api";



type ResearchType = "stock" | "portfolio" | "topic";

interface ResearchToggleProps {
  type: ResearchType;
  /** Stock ticker (for type="stock") */
  ticker?: string;
  /** Portfolio ID (for type="portfolio") */
  portfolioId?: string;
  /** Topic query (for type="topic") */
  topic?: string;
  /** Compact mode for inline placement */
  compact?: boolean;
}

export function ResearchToggle({
  type,
  ticker,
  portfolioId,
  topic,
  compact = false,
}: ResearchToggleProps) {
  const [taskId, setTaskId] = useState<string | null>(null);
  const [isComplete, setIsComplete] = useState(false);

  // Mutation to trigger research
  const triggerMutation = useMutation({
    mutationFn: async () => {
      switch (type) {
        case "stock":
          if (!ticker) throw new Error("Ticker required");
          return researchStock(ticker);
        case "portfolio":
          if (!portfolioId) throw new Error("Portfolio ID required");
          return researchPortfolio(portfolioId);
        case "topic":
          if (!topic) throw new Error("Topic required");
          return researchTopic(topic);
      }
    },
    onSuccess: (data) => {
      setTaskId(data.task_id);
    },
  });

  // Poll for task status
  const { data: statusData } = useQuery({
    queryKey: ["research-status", taskId],
    queryFn: () => getResearchStatus(taskId!),
    enabled: !!taskId && !isComplete,
    refetchInterval: (query) => {
      const state = query.state.data?.status;
      if (state === "SUCCESS" || state === "FAILURE") {
        setIsComplete(true);
        return false;
      }
      return 3000; // Poll every 3 seconds
    },
  });

  const isRunning = triggerMutation.isPending || (!!taskId && !isComplete);
  const status = statusData?.status;
  const progress = statusData?.progress as Record<string, unknown> | null;

  const handleTrigger = () => {
    setIsComplete(false);
    setTaskId(null);
    triggerMutation.mutate();
  };

  if (compact) {
    return (
      <div className="flex items-center gap-3">
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant={isRunning ? "secondary" : "outline"}
                size="sm"
                onClick={handleTrigger}
                disabled={isRunning}
                className="gap-1.5"
              >
                {isRunning ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : isComplete && status === "SUCCESS" ? (
                  <CheckCircle2 className="h-3.5 w-3.5 text-green-600" />
                ) : isComplete && status === "FAILURE" ? (
                  <XCircle className="h-3.5 w-3.5 text-red-600" />
                ) : (
                  <Sparkles className="h-3.5 w-3.5" />
                )}
                {isRunning
                  ? "Researching..."
                  : isComplete
                    ? status === "SUCCESS"
                      ? "Done"
                      : "Retry"
                    : "Deep Research"}
              </Button>
            </TooltipTrigger>
            <TooltipContent side="bottom" className="max-w-[240px]">
              <p className="text-xs">
                Uses Firecrawl, Browse.ai & Thunderbit to find additional news
                articles and analysis from across the web.
              </p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>

        {isRunning && progress && (
          <span className="text-xs text-muted-foreground">
            {(progress as Record<string, unknown>)?.stage as string || "Processing..."}
          </span>
        )}
      </div>
    );
  }

  return (
    <Card>
      <CardContent className="py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Sparkles className="h-5 w-5 text-primary" />
            <div>
              <Label className="text-sm font-medium">
                Extensive Research
              </Label>
              <p className="text-xs text-muted-foreground mt-0.5">
                Deep web search using AI-powered scrapers for comprehensive
                coverage
              </p>
            </div>
          </div>

          <Button
            onClick={handleTrigger}
            disabled={isRunning}
            size="sm"
            variant={isRunning ? "secondary" : "default"}
            className="gap-1.5"
          >
            {isRunning ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Search className="h-4 w-4" />
            )}
            {isRunning ? "Researching..." : "Start Research"}
          </Button>
        </div>

        {/* Progress/Status section */}
        {(isRunning || isComplete) && (
          <div className="mt-4 space-y-2">
            {isRunning && !isComplete && (
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>
                    {(progress as Record<string, unknown>)?.stage as string ||
                      "Initializing research..."}
                  </span>
                  {progress?.articles_found != null && (
                    <span>
                      {String(progress.articles_found)} articles found
                    </span>
                  )}
                </div>
                <Progress value={undefined} className="h-1.5" />
              </div>
            )}

            {isComplete && status === "SUCCESS" && (
              <div className="flex items-center gap-2 text-sm text-green-600">
                <CheckCircle2 className="h-4 w-4" />
                <span>
                  Research complete
                  {statusData?.result?.new_articles != null &&
                    ` — ${statusData.result.new_articles} new articles found`}
                </span>
              </div>
            )}

            {isComplete && status === "FAILURE" && (
              <div className="flex items-center gap-2 text-sm text-red-600">
                <XCircle className="h-4 w-4" />
                <span>
                  Research failed
                  {statusData?.error && `: ${statusData.error}`}
                </span>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
