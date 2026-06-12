"use client";

import { useEffect, useRef, useState } from "react";
import { getStatus } from "../api/videos";
import type { StatusResponse } from "../api/types";
import { POLL_INTERVAL_MS } from "../constants";

interface UseJobPollerResult {
  status: StatusResponse;
  error: string | null;
  isLoading: boolean;
}

export function useJobPoller(
  jobId: string,
  initialStatus: StatusResponse
): UseJobPollerResult {
  const [status, setStatus] = useState<StatusResponse>(initialStatus);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    const terminal = status.status === "completed" || status.status === "failed";
    if (terminal) return;

    intervalRef.current = setInterval(async () => {
      setIsLoading(true);
      try {
        const next = await getStatus(jobId);
        setStatus(next);
        if (next.status === "completed" || next.status === "failed") {
          clearInterval(intervalRef.current!);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to fetch status.");
        clearInterval(intervalRef.current!);
      } finally {
        setIsLoading(false);
      }
    }, POLL_INTERVAL_MS);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [jobId, status.status]);

  return { status, error, isLoading };
}
