from uuid import UUID

from pydantic import BaseModel


class TimelineEvent(BaseModel):
    timestamp: float
    event: str


class SummaryResponse(BaseModel):
    job_id: UUID
    summary: str
    model_used: str | None = None


class TimelineResponse(BaseModel):
    job_id: UUID
    timeline: list[TimelineEvent]
