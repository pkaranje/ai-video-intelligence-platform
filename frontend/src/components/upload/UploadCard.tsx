"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useUpload } from "@/lib/hooks/useUpload";
import { FileDropzone } from "./FileDropzone";
import { UploadProgress } from "./UploadProgress";
import { Card } from "@/components/ui/Card";
import { ErrorBanner } from "@/components/job/ErrorBanner";

export function UploadCard() {
  const router = useRouter();
  const { state, jobId, uploadProgress, error, upload } = useUpload();

  useEffect(() => {
    if (state === "done" && jobId) {
      router.push(`/jobs/${jobId}`);
    }
  }, [state, jobId, router]);

  const busy = state === "uploading" || state === "polling";

  return (
    <Card className="w-full max-w-lg p-6">
      <h1 className="mb-4 text-xl font-semibold text-zinc-900 dark:text-zinc-100">
        Upload a Video
      </h1>

      <div className="flex flex-col gap-4">
        <FileDropzone onFileAccepted={upload} disabled={busy} />

        {state === "uploading" && <UploadProgress percent={uploadProgress} />}

        {state === "polling" && (
          <p className="text-sm text-zinc-500">Processing your video…</p>
        )}

        <ErrorBanner message={error} />
      </div>
    </Card>
  );
}
