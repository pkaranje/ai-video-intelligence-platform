function SkeletonBlock({ className }: { className?: string }) {
  return (
    <div className={`animate-pulse rounded bg-zinc-200 dark:bg-zinc-700 ${className ?? ""}`} />
  );
}

export default function Loading() {
  return (
    <main className="mx-auto w-full max-w-2xl px-4 py-12">
      {/* Page header skeleton */}
      <div className="mb-6 flex flex-col gap-2">
        <SkeletonBlock className="h-3 w-64" />
        <SkeletonBlock className="h-7 w-32" />
      </div>

      {/* Status card skeleton */}
      <div className="flex flex-col gap-4 rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-700 dark:bg-zinc-900">
        <div className="flex items-center gap-3">
          <SkeletonBlock className="h-5 w-28 rounded-full" />
          <SkeletonBlock className="h-4 w-4 rounded-full" />
        </div>
        <div className="flex justify-between">
          <SkeletonBlock className="h-3 w-16" />
          <SkeletonBlock className="h-3 w-8" />
        </div>
        <SkeletonBlock className="h-2 w-full rounded-full" />
      </div>
    </main>
  );
}
