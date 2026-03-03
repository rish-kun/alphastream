import { ResearchResultsPageClient } from "@/components/research/research-results-page-client";

interface ResearchResultsPageProps {
  params: Promise<{ taskId: string }>;
}

export default async function ResearchResultsPage({
  params,
}: ResearchResultsPageProps) {
  const { taskId } = await params;
  return <ResearchResultsPageClient taskId={taskId} />;
}
