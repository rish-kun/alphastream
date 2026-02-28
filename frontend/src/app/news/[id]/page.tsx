"use client";

import { use } from "react";
import { useQuery } from "@tanstack/react-query";
import { NewsDetail } from "@/components/news/news-detail";
import { NewsCard } from "@/components/news/news-card";
import { Skeleton } from "@/components/ui/skeleton";
import { getNewsFeed } from "@/lib/api";
import type { NewsArticleDetail } from "@/types/news";

interface NewsDetailPageProps {
  params: Promise<{ id: string }>;
}

export default function NewsDetailPage({ params }: NewsDetailPageProps) {
  const { id } = use(params);

  return (
    <div className="mx-auto max-w-4xl space-y-8">
      <NewsDetail id={id} />
      <RelatedArticles articleId={id} />
    </div>
  );
}

function RelatedArticles({ articleId }: { articleId: string }) {
  // Fetch first page of news to show as "related" articles
  // In production this would be a dedicated endpoint
  const { data, isLoading } = useQuery({
    queryKey: ["related-articles", articleId],
    queryFn: () => getNewsFeed({ page: 1, size: 5 }),
    staleTime: 5 * 60 * 1000,
  });

  const articles =
    data?.items?.filter((a) => a.id !== articleId).slice(0, 4) ?? [];

  if (isLoading) {
    return (
      <div className="space-y-3">
        <h2 className="text-lg font-semibold">Related Articles</h2>
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-20 w-full rounded-lg" />
        ))}
      </div>
    );
  }

  if (articles.length === 0) return null;

  return (
    <div className="space-y-3">
      <h2 className="text-lg font-semibold">Related Articles</h2>
      {articles.map((article) => (
        <NewsCard key={article.id} article={article} variant="compact" />
      ))}
    </div>
  );
}
