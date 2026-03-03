"use client";

import { useEffect, type ComponentType } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Clock, Gauge, Loader2, Sparkles, Timer } from "lucide-react";

import { getResearchStatus } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

interface ResearchStatusPageClientProps {
  taskId: string;
}

function formatDuration(seconds: number | null | undefined): string {
  if (seconds == null) return "--";
  if (seconds < 60) return `${seconds}s`;
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}m ${secs}s`;
}

export function ResearchStatusPageClient({
  taskId,
}: ResearchStatusPageClientProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const topic = searchParams.get("topic") ?? "";

  const statusQuery = useQuery({
    queryKey: ["research-status-page", taskId],
    queryFn: () => getResearchStatus(taskId),
    refetchInterval: (query) => {
      const state = query.state.data?.status;
      if (state === "SUCCESS" || state === "FAILURE") return false;
      return 2500;
    },
  });

  const status = statusQuery.data?.status;
  const progress = statusQuery.data?.progress;
  const percent =
    typeof progress?.percent_complete === "number" ? progress.percent_complete : 0;
  const queryIndex =
    typeof progress?.query_index === "number" ? progress.query_index : null;
  const totalQueries =
    typeof progress?.total_queries === "number" ? progress.total_queries : null;
  const etaSeconds =
    typeof progress?.eta_seconds === "number" ? progress.eta_seconds : null;
  const elapsedSeconds =
    typeof progress?.elapsed_seconds === "number" ? progress.elapsed_seconds : null;
  const ballparkLow =
    typeof progress?.expected_new_articles_low === "number"
      ? progress.expected_new_articles_low
      : null;
  const ballparkHigh =
    typeof progress?.expected_new_articles_high === "number"
      ? progress.expected_new_articles_high
      : null;

  useEffect(() => {
    if (status !== "SUCCESS") return;
    const taskResult = statusQuery.data?.result;
    if (!taskResult || typeof taskResult !== "object") return;
    const taskState = (taskResult as Record<string, unknown>).status;
    if (taskState !== "completed") return;
    const params = new URLSearchParams();
    if (topic) params.set("topic", topic);
    const suffix = params.toString();
    router.replace(`/news/research/${taskId}/results${suffix ? `?${suffix}` : ""}`);
  }, [router, status, statusQuery.data?.result, taskId, topic]);

  if (statusQuery.isLoading) {
    return (
      <div className="mx-auto max-w-3xl space-y-4">
        <h1 className="text-2xl font-bold">Deep Research Status</h1>
        <Card>
          <CardContent className="py-8">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading status...
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (status === "FAILURE") {
    return (
      <div className="mx-auto max-w-3xl space-y-4">
        <h1 className="text-2xl font-bold">Deep Research Status</h1>
        <Card>
          <CardHeader>
            <CardTitle>Research Failed</CardTitle>
            <CardDescription>
              {statusQuery.data?.error ?? "Unknown error"}
            </CardDescription>
          </CardHeader>
          <CardContent className="flex gap-2">
            <Button asChild variant="outline">
              <Link href="/news">Back to News</Link>
            </Button>
            {topic ? (
              <Button asChild>
                <Link href={`/news?search=${encodeURIComponent(topic)}`}>Try Again</Link>
              </Button>
            ) : null}
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <div className="space-y-1">
        <h1 className="text-2xl font-bold">Deep Research Status</h1>
        <p className="text-sm text-muted-foreground">
          {topic ? `Researching topic: ${topic}` : "Research in progress"}
        </p>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-4 w-4" />
                Live Progress
              </CardTitle>
              <CardDescription>
                {typeof progress?.stage === "string"
                  ? progress.stage
                  : "Initializing research"}
              </CardDescription>
            </div>
            <Badge>{status ?? "PENDING"}</Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>
                {queryIndex && totalQueries
                  ? `Query ${queryIndex} of ${totalQueries}`
                  : "Preparing search queries"}
              </span>
              <span>{percent.toFixed(0)}%</span>
            </div>
            <Progress value={percent} className="h-2" />
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            <Metric label="Elapsed" value={formatDuration(elapsedSeconds)} icon={Clock} />
            <Metric label="ETA" value={formatDuration(etaSeconds)} icon={Timer} />
            <Metric
              label="Ballpark New Articles"
              value={
                ballparkLow != null && ballparkHigh != null
                  ? `${ballparkLow}-${ballparkHigh}`
                  : "--"
              }
              icon={Gauge}
            />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function Metric({
  label,
  value,
  icon: Icon,
}: {
  label: string;
  value: string;
  icon: ComponentType<{ className?: string }>;
}) {
  return (
    <Card>
      <CardContent className="py-3">
        <p className="mb-2 flex items-center gap-1.5 text-xs text-muted-foreground">
          <Icon className="h-3.5 w-3.5" />
          {label}
        </p>
        <p className="text-sm font-semibold">{value}</p>
      </CardContent>
    </Card>
  );
}
