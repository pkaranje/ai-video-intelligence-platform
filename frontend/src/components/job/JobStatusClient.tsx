"use client";

import { useEffect, useState } from "react";
import { useJobPoller } from "@/lib/hooks/useJobPoller";
import { getSummary, getTimeline } from "@/lib/api/videos";
import type { StatusResponse, SummaryResponse, TimelineResponse } from "@/lib/api/types";
import { StageBadge } from "./StageBadge";
import { ErrorBanner } from "./ErrorBanner";
import { SummaryCard } from "@/components/summary/SummaryCard";
import { TimelineList } from "@/components/summary/TimelineList";
import { Spinner } from "@/components/ui/Spinner";

interface JobStatusClientProps {
  jobId: string;
  initialStatus: StatusResponse;
}

export function JobStatusClient({ jobId, initialStatus }: JobStatusClientProps) {
  const { status, error } = useJobPoller(jobId, initialStatus);
  const [summary, setSummary] = useState<SummaryResponse | null>(null);
  const [timeline, setTimeline] = useState<TimelineResponse | null>(null);
  const [resultsError, setResultsError] = useState<string | null>(null);

  useEffect(() => {
    if (status.status !== "completed") return;
    let cancelled = false;
    async function fetchResults() {
      try {
        const [s, t] = await Promise.all([getSummary(jobId), getTimeline(jobId)]);
        if (!cancelled) {
          setSummary(s);
          setTimeline(t);
        }
      } catch (err) {
        if (!cancelled) {
          setResultsError(err instanceof Error ? err.message : "Failed to load results.");
        }
      }
    }
    fetchResults();
    return () => { cancelled = true; };
  }, [jobId, status.status]);

  const isTerminal = status.status === "completed" || status.status === "failed";
  const progress = Math.max(0, Math.min(100, status.progress_pct));

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-3 rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-700 dark:bg-zinc-900">
        <div className="flex items-center gap-3">
          <StageBadge stage={status.stage} />
          {!isTerminal && <Spinner size="sm" />}
        </div>

        <div className="flex items-center justify-between text-xs text-zinc-500">
          <span className="capitalize">{status.status}</span>
          <span>{progress}%</span>
        </div>
        <div className="h-2 w-full overflow-hidden rounded-full bg-zinc-100 dark:bg-zinc-800">
          <div
            className={`h-full rounded-full transition-all duration-500 ${
              status.status === "failed"
                ? "bg-red-500"
                : status.status === "completed"
                ? "bg-green-500"
                : "bg-zinc-900 dark:bg-zinc-50"
            }`}
            style={{ width: `${progress}%` }}
          />
        </div>

        <ErrorBanner message={error ?? status.error_message} />
      </div>

      {resultsError && <ErrorBanner message={resultsError} />}

      {summary && <SummaryCard summary={summary} />}
      {timeline && <TimelineList events={timeline.timeline} />}
    </div>
  );
}
