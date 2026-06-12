import { Card } from "@/components/ui/Card";
import type { SummaryResponse } from "@/lib/api/types";

interface SummaryCardProps {
  summary: SummaryResponse;
}

export function SummaryCard({ summary }: SummaryCardProps) {
  const wordCount = summary.summary.trim().split(/\s+/).filter(Boolean).length;
  const generatedAt = new Date(summary.generated_at).toLocaleString();

  return (
    <Card className="p-6">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-base font-semibold text-zinc-900 dark:text-zinc-100">Summary</h2>
        <span className="text-xs text-zinc-400">{wordCount} words · {generatedAt}</span>
      </div>
      <p className="text-sm leading-7 text-zinc-700 dark:text-zinc-300 whitespace-pre-wrap">
        {summary.summary}
      </p>
    </Card>
  );
}
