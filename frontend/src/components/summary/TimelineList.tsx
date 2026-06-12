import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { formatTimestamp } from "@/lib/utils/format";
import type { TimelineEvent } from "@/lib/api/types";

interface TimelineListProps {
  events: TimelineEvent[];
}

export function TimelineList({ events }: TimelineListProps) {
  if (events.length === 0) {
    return (
      <Card className="p-6">
        <p className="text-sm text-zinc-500">No timeline events.</p>
      </Card>
    );
  }

  return (
    <Card className="p-6">
      <h2 className="mb-4 text-base font-semibold text-zinc-900 dark:text-zinc-100">Timeline</h2>
      <ol className="flex flex-col gap-3">
        {events.map((event, i) => (
          <li key={i} className="flex items-start gap-3">
            <Badge variant="grey" className="shrink-0 font-mono">
              {formatTimestamp(event.timestamp)}
            </Badge>
            <span className="text-sm text-zinc-700 dark:text-zinc-300">{event.description}</span>
          </li>
        ))}
      </ol>
    </Card>
  );
}
