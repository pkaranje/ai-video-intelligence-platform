from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


class JobStatus(StrEnum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class ProgressStage(StrEnum):
    upload_validation = "upload_validation"
    frame_extraction = "frame_extraction"
    ai_analysis = "ai_analysis"
    aggregation = "aggregation"
    completed = "completed"


class UploadResponse(BaseModel):
    job_id: UUID
    status: JobStatus
    message: str


class StatusResponse(BaseModel):
    job_id: UUID
    status: JobStatus
    stage: ProgressStage | None = None
    progress_pct: int
    error_message: str | None = None
