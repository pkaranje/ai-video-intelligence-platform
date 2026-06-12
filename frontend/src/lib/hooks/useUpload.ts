"use client";

import { useState } from "react";
import type { StatusResponse, UploadResponse } from "../api/types";
import { getStatus } from "../api/videos";
import { POLL_INTERVAL_MS } from "../constants";
import { validateFileSize, validateFileType } from "../utils/validation";

type UploadState = "idle" | "uploading" | "polling" | "done" | "error";

interface UseUploadResult {
  state: UploadState;
  jobId: string | null;
  uploadProgress: number;
  finalStatus: StatusResponse | null;
  error: string | null;
  upload: (file: File) => void;
}

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "/api/proxy";

export function useUpload(): UseUploadResult {
  const [state, setState] = useState<UploadState>("idle");
  const [jobId, setJobId] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [finalStatus, setFinalStatus] = useState<StatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  function upload(file: File) {
    const typeCheck = validateFileType(file);
    if (!typeCheck.valid) {
      setError(typeCheck.message ?? "Invalid file type.");
      setState("error");
      return;
    }
    const sizeCheck = validateFileSize(file);
    if (!sizeCheck.valid) {
      setError(sizeCheck.message ?? "File too large.");
      setState("error");
      return;
    }

    setState("uploading");
    setUploadProgress(0);
    setError(null);

    const form = new FormData();
    form.append("file", file);

    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${BASE}/api/v1/videos`);

    xhr.upload.addEventListener("progress", (e) => {
      if (e.lengthComputable) {
        setUploadProgress(Math.round((e.loaded / e.total) * 100));
      }
    });

    xhr.addEventListener("load", () => {
      if (xhr.status === 202) {
        let response: UploadResponse;
        try {
          response = JSON.parse(xhr.responseText) as UploadResponse;
        } catch {
          setError("Invalid response from server.");
          setState("error");
          return;
        }
        setJobId(response.job_id);
        setState("polling");
        startPolling(response.job_id);
      } else {
        let message = xhr.statusText;
        try {
          const body = JSON.parse(xhr.responseText);
          message = body.detail ?? body.message ?? message;
        } catch {
          // ignore
        }
        setError(message);
        setState("error");
      }
    });

    xhr.addEventListener("error", () => {
      setError("Upload failed due to a network error.");
      setState("error");
    });

    xhr.send(form);
  }

  function startPolling(id: string) {
    const interval = setInterval(async () => {
      try {
        const status = await getStatus(id);
        if (status.status === "completed" || status.status === "failed") {
          clearInterval(interval);
          setFinalStatus(status);
          setState("done");
        }
      } catch (err) {
        clearInterval(interval);
        setError(err instanceof Error ? err.message : "Failed to fetch status.");
        setState("error");
      }
    }, POLL_INTERVAL_MS);
  }

  return { state, jobId, uploadProgress, finalStatus, error, upload };
}
