export type JobStatus = "queued" | "running" | "completed" | "failed";

export type ProgressStage =
  | "upload_validation"
  | "frame_extraction"
  | "ai_analysis"
  | "aggregation"
  | "completed";

export interface UploadResponse {
  job_id: string;
}

export interface StatusResponse {
  job_id: string;
  status: JobStatus;
  stage: ProgressStage;
  progress_pct: number;
  error_message: string | null;
}

export interface TimelineEvent {
  timestamp: number;
  description: string;
}

export interface SummaryResponse {
  job_id: string;
  summary: string;
  model_used: string;
  generated_at: string;
}

export interface TimelineResponse {
  job_id: string;
  timeline: TimelineEvent[];
}

export class APIError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "APIError";
    this.status = status;
  }
}
