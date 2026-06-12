import { UploadCard } from "@/components/upload/UploadCard";

export default function Home() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center px-4 py-16">
      <div className="mb-10 text-center">
        <h1 className="text-4xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
          AI Video Intelligence
        </h1>
        <p className="mt-3 text-base text-zinc-500 dark:text-zinc-400">
          Upload an MP4 and get an AI-generated summary with a timestamped event timeline.
        </p>
      </div>
      <UploadCard />
    </main>
  );
}
