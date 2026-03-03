"use client";

import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { Loader2, Sparkles } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { researchTopic } from "@/lib/api";

interface TopicResearchButtonProps {
  topic: string;
}

export function TopicResearchButton({ topic }: TopicResearchButtonProps) {
  const router = useRouter();

  const dispatchMutation = useMutation({
    mutationFn: async () => researchTopic(topic),
    onSuccess: (data) => {
      const params = new URLSearchParams({ topic });
      router.push(`/news/research/${data.task_id}?${params.toString()}`);
    },
    onError: (error) => {
      toast.error(
        error instanceof Error ? error.message : "Failed to start research"
      );
    },
  });

  return (
    <div className="flex items-center gap-3">
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant={dispatchMutation.isPending ? "secondary" : "outline"}
              size="sm"
              onClick={() => dispatchMutation.mutate()}
              disabled={dispatchMutation.isPending}
              className="gap-1.5"
            >
              {dispatchMutation.isPending ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <Sparkles className="h-3.5 w-3.5" />
              )}
              {dispatchMutation.isPending ? "Starting..." : "Deep Research"}
            </Button>
          </TooltipTrigger>
          <TooltipContent side="bottom" className="max-w-[260px]">
            <p className="text-xs">
              Launches live deep research for this topic and opens a status page
              with progress, ETA, and article estimates.
            </p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    </div>
  );
}
