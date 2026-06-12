import { fetchAPI } from "./client";
import type {
  UploadResponse,
  StatusResponse,
  SummaryResponse,
  TimelineResponse,
} from "./types";

export function uploadVideo(file: File): Promise<UploadResponse> {
  const form = new FormData();
  form.append("file", file);
  return fetchAPI<UploadResponse>("/api/v1/videos", {
    method: "POST",
    body: form,
  });
}

export function getStatus(jobId: string): Promise<StatusResponse> {
  return fetchAPI<StatusResponse>(`/api/v1/videos/${jobId}/status`);
}

export function getSummary(jobId: string): Promise<SummaryResponse> {
  return fetchAPI<SummaryResponse>(`/api/v1/videos/${jobId}/summary`);
}

export function getTimeline(jobId: string): Promise<TimelineResponse> {
  return fetchAPI<TimelineResponse>(`/api/v1/videos/${jobId}/timeline`);
}
