import { Suspense } from "react";
import { notFound } from "next/navigation";
import { JobStatusClient } from "@/components/job/JobStatusClient";
import type { StatusResponse } from "@/lib/api/types";
import { APIError } from "@/lib/api/types";

interface PageProps {
  params: Promise<{ jobId: string }>;
}

function StatusSkeleton() {
  return (
    <div className="flex flex-col gap-4 rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-700 dark:bg-zinc-900">
      {["w-28", "w-full", "w-16"].map((w) => (
        <div
          key={w}
          className={`animate-pulse rounded bg-zinc-200 dark:bg-zinc-700 h-4 ${w}`}
        />
      ))}
    </div>
  );
}

async function StatusLoader({ jobId }: { jobId: string }) {
  const backendUrl = process.env.BACKEND_URL ?? "http://localhost:8000";
  const res = await fetch(`${backendUrl}/api/v1/videos/${jobId}/status`, {
    cache: "no-store",
  });

  if (res.status === 404) notFound();
  if (!res.ok) {
    let message = res.statusText;
    try {
      const body = (await res.json()) as { detail?: string; message?: string };
      message = body.detail ?? body.message ?? message;
    } catch {
      // ignore parse error
    }
    throw new APIError(message, res.status);
  }

  const initialStatus = (await res.json()) as StatusResponse;
  return <JobStatusClient jobId={jobId} initialStatus={initialStatus} />;
}

export default async function JobPage({ params }: PageProps) {
  const { jobId } = await params;

  return (
    <main className="mx-auto w-full max-w-2xl px-4 py-12">
      <div className="mb-6">
        <p className="font-mono text-xs text-zinc-400">{jobId}</p>
        <h1 className="mt-1 text-2xl font-semibold text-zinc-900 dark:text-zinc-100">
          Job Status
        </h1>
      </div>
      <Suspense fallback={<StatusSkeleton />}>
        <StatusLoader jobId={jobId} />
      </Suspense>
    </main>
  );
}
