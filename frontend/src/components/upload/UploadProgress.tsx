"use client";

interface UploadProgressProps {
  percent: number;
}

export function UploadProgress({ percent }: UploadProgressProps) {
  const clamped = Math.max(0, Math.min(100, percent));
  return (
    <div className="w-full">
      <div className="mb-1 flex justify-between text-xs text-zinc-500">
        <span>Uploading…</span>
        <span>{clamped}%</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-700">
        <div
          className="h-full rounded-full bg-zinc-900 transition-all duration-200 dark:bg-zinc-50"
          style={{ width: `${clamped}%` }}
        />
      </div>
    </div>
  );
}
