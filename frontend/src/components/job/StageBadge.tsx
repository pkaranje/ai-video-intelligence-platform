import { Badge } from "@/components/ui/Badge";
import type { ProgressStage } from "@/lib/api/types";

const stageVariant: Record<ProgressStage, "grey" | "blue" | "purple" | "amber" | "green"> = {
  upload_validation: "grey",
  frame_extraction: "blue",
  ai_analysis: "purple",
  aggregation: "amber",
  completed: "green",
};

const stageLabel: Record<ProgressStage, string> = {
  upload_validation: "Upload Validation",
  frame_extraction: "Frame Extraction",
  ai_analysis: "AI Analysis",
  aggregation: "Aggregation",
  completed: "Completed",
};

interface StageBadgeProps {
  stage: ProgressStage;
}

export function StageBadge({ stage }: StageBadgeProps) {
  return <Badge variant={stageVariant[stage]}>{stageLabel[stage]}</Badge>;
}
