import { notFound } from "next/navigation";
import { JobStatusClient } from "@/components/job/JobStatusClient";
import type { StatusResponse } from "@/lib/api/types";
import { APIError } from "@/lib/api/types";

interface PageProps {
  params: Promise<{ jobId: string }>;
}

async function fetchInitialStatus(jobId: string): Promise<StatusResponse> {
  const backendUrl = process.env.BACKEND_URL ?? "http://localhost:8000";
  const res = await fetch(`${backendUrl}/api/v1/videos/${jobId}/status`, {
    cache: "no-store",
  });
  if (res.status === 404) notFound();
  if (!res.ok) {
    let message = res.statusText;
    try {
      const body = await res.json();
      message = body.detail ?? body.message ?? message;
    } catch {
      // ignore
    }
    throw new APIError(message, res.status);
  }
  return res.json() as Promise<StatusResponse>;
}

export default async function JobPage({ params }: PageProps) {
  const { jobId } = await params;
  const initialStatus = await fetchInitialStatus(jobId);

  return (
    <main className="mx-auto w-full max-w-2xl px-4 py-12">
      <div className="mb-6">
        <p className="text-xs text-zinc-400 font-mono">{jobId}</p>
        <h1 className="mt-1 text-2xl font-semibold text-zinc-900 dark:text-zinc-100">
          Job Status
        </h1>
      </div>
      <JobStatusClient jobId={jobId} initialStatus={initialStatus} />
    </main>
  );
}
