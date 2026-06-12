import { Spinner } from "@/components/ui/Spinner";

export default function Loading() {
  return (
    <main className="flex flex-1 items-center justify-center py-24">
      <Spinner size="lg" />
    </main>
  );
}
