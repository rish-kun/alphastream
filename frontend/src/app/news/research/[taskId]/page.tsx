import { ResearchStatusPageClient } from "@/components/research/research-status-page-client";

interface ResearchStatusPageProps {
  params: Promise<{ taskId: string }>;
}

export default async function ResearchStatusPage({
  params,
}: ResearchStatusPageProps) {
  const { taskId } = await params;
  return <ResearchStatusPageClient taskId={taskId} />;
}
