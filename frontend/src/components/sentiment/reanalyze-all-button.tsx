"use client";

import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, RotateCcw } from "lucide-react";
import { toast } from "sonner";

import { getReanalyzeAllStatus, reanalyzeAllSentiment } from "@/lib/api";
import { SidebarMenuButton } from "@/components/ui/sidebar";

export function ReanalyzeAllButton() {
  const queryClient = useQueryClient();
  const [taskId, setTaskId] = useState<string | null>(null);

  const dispatchMutation = useMutation({
    mutationFn: async () => {
      const confirmed = window.confirm(
        "Reanalyze sentiment for all news articles? This can queue many tasks.",
      );
      if (!confirmed) {
        throw new Error("cancelled_by_user");
      }
      return reanalyzeAllSentiment();
    },
    onSuccess: (result) => {
      setTaskId(result.task_id);
      toast.success("Queued reanalysis for all articles");
    },
    onError: (error) => {
      if (error instanceof Error && error.message === "cancelled_by_user") {
        return;
      }
      toast.error(
        error instanceof Error ? error.message : "Failed to start reanalysis",
      );
    },
  });

  const statusQuery = useQuery({
    queryKey: ["reanalyze-all-status", taskId],
    queryFn: async () => {
      if (!taskId) {
        throw new Error("Missing task id");
      }
      return getReanalyzeAllStatus(taskId);
    },
    enabled: Boolean(taskId),
    refetchInterval: (query) => {
      const state = query.state.data?.status;
      if (!state || state === "PENDING" || state === "PROGRESS") {
        return 2500;
      }
      return false;
    },
  });

  const status = statusQuery.data?.status;
  const dispatched = useMemo(() => {
    const progressValue = statusQuery.data?.progress?.dispatched;
    if (typeof progressValue === "number") {
      return progressValue;
    }
    const resultValue = statusQuery.data?.result?.dispatched;
    if (typeof resultValue === "number") {
      return resultValue;
    }
    return null;
  }, [statusQuery.data]);

  const targeted = useMemo(() => {
    const progressValue = statusQuery.data?.progress?.targeted_articles;
    if (typeof progressValue === "number") {
      return progressValue;
    }
    const resultValue = statusQuery.data?.result?.targeted_articles;
    if (typeof resultValue === "number") {
      return resultValue;
    }
    return null;
  }, [statusQuery.data]);

  useEffect(() => {
    if (status !== "SUCCESS") {
      return;
    }
    toast.success("Reanalysis queue completed");
    void queryClient.invalidateQueries({ queryKey: ["news"] });
    void queryClient.invalidateQueries({ queryKey: ["trending-news"] });
    void queryClient.invalidateQueries({ queryKey: ["sentiment"] });
    void queryClient.invalidateQueries({ queryKey: ["top-signals"] });
  }, [queryClient, status]);

  useEffect(() => {
    if (status !== "FAILURE") {
      return;
    }
    toast.error(statusQuery.data?.error ?? "Reanalysis queue failed");
  }, [status, statusQuery.data?.error]);

  const isBusy =
    dispatchMutation.isPending || status === "PENDING" || status === "PROGRESS";
  const label = isBusy
    ? dispatched !== null && targeted !== null
      ? `Reanalyzing ${dispatched}/${targeted}`
      : "Reanalyzing..."
    : "Reanalyze Everything";

  return (
    <SidebarMenuButton
      onClick={() => dispatchMutation.mutate()}
      disabled={isBusy}
      tooltip={label}
    >
      {isBusy ? (
        <Loader2 className="h-4 w-4 animate-spin" />
      ) : (
        <RotateCcw className="h-4 w-4" />
      )}
      <span>{label}</span>
    </SidebarMenuButton>
  );
}
