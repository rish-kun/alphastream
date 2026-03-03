"use client";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Tags } from "lucide-react";
import { getTrendingNews } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

const TOPIC_KEYWORDS: Array<{ topic: string; keywords: string[] }> = [
  {
    topic: "Metals & Mining",
    keywords: ["steel", "gold", "silver", "copper", "zinc", "mining", "ore", "metal"],
  },
  {
    topic: "Energy",
    keywords: ["oil", "gas", "crude", "power", "renewable", "solar", "wind", "coal"],
  },
  {
    topic: "Banking & Finance",
    keywords: ["bank", "nbfc", "credit", "loan", "rbi", "interest", "bond", "yield"],
  },
  {
    topic: "Technology",
    keywords: ["ai", "software", "it services", "cloud", "semiconductor", "digital"],
  },
  {
    topic: "Automotive",
    keywords: ["auto", "automobile", "ev", "vehicle", "car", "two-wheeler"],
  },
  {
    topic: "Macroeconomy",
    keywords: ["inflation", "gdp", "deficit", "rupee", "budget", "policy", "economy"],
  },
];

function formatTimeAgo(isoDate: string): string {
  const date = new Date(isoDate).getTime();
  if (Number.isNaN(date)) return "unknown";

  const minutes = Math.floor((Date.now() - date) / 60_000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;

  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;

  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

function resolveTopicName(article: {
  title: string;
  summary?: string | null;
  category?: string | null;
}): string {
  if (article.category?.trim()) return article.category.trim();

  const searchableText = `${article.title} ${article.summary ?? ""}`.toLowerCase();
  const matchedTopic = TOPIC_KEYWORDS.find((entry) =>
    entry.keywords.some((keyword) => searchableText.includes(keyword))
  );

  return matchedTopic?.topic ?? "General";
}

interface TopicBucket {
  topic: string;
  count: number;
  latestPublishedAt: string;
  sourceCount: number;
}

export function TopicOverview() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["trending-news", "topic-overview"],
    queryFn: () => getTrendingNews(100),
    staleTime: 5 * 60 * 1000,
  });

  const topicBuckets = useMemo<TopicBucket[]>(() => {
    const buckets = new Map<
      string,
      { count: number; latestPublishedAt: string; sources: Set<string> }
    >();

    for (const article of data?.articles ?? []) {
      const topic = resolveTopicName(article);
      const existing = buckets.get(topic);

      if (!existing) {
        buckets.set(topic, {
          count: 1,
          latestPublishedAt: article.published_at,
          sources: new Set([article.source]),
        });
        continue;
      }

      existing.count += 1;
      existing.sources.add(article.source);
      if (
        new Date(article.published_at).getTime() >
        new Date(existing.latestPublishedAt).getTime()
      ) {
        existing.latestPublishedAt = article.published_at;
      }
    }

    return Array.from(buckets.entries())
      .map(([topic, value]) => ({
        topic,
        count: value.count,
        latestPublishedAt: value.latestPublishedAt,
        sourceCount: value.sources.size,
      }))
      .sort((a, b) => b.count - a.count || a.topic.localeCompare(b.topic));
  }, [data?.articles]);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Tags className="h-5 w-5" />
          Analyzed Topics
        </CardTitle>
        <p className="text-sm text-muted-foreground">
          Topic categories from recently analyzed articles
        </p>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-2">
            {Array.from({ length: 5 }).map((_, index) => (
              <Skeleton key={index} className="h-14 w-full rounded-lg" />
            ))}
          </div>
        ) : isError || topicBuckets.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No categorized topics available yet.
          </p>
        ) : (
          <div className="space-y-2">
            {topicBuckets.slice(0, 10).map((bucket) => (
              <div
                key={bucket.topic}
                className="flex items-center justify-between rounded-lg border p-3"
              >
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium">{bucket.topic}</p>
                  <p className="text-xs text-muted-foreground">
                    {bucket.sourceCount} source{bucket.sourceCount === 1 ? "" : "s"} · updated {formatTimeAgo(bucket.latestPublishedAt)}
                  </p>
                </div>
                <Badge variant="secondary">
                  {bucket.count} article{bucket.count === 1 ? "" : "s"}
                </Badge>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
