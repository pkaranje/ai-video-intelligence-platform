from sqlalchemy import select

from api.db.models import VideoSummary
from api.domain.video import JobNotFoundError, SummaryNotReadyError
from api.repositories.job_repo import JobRepository
from api.schemas.summary import SummaryResponse, TimelineEvent, TimelineResponse
from api.services import BaseService
from sqlalchemy.ext.asyncio import AsyncSession


class SummaryService(BaseService):
    def __init__(self, session: AsyncSession, job_repo: JobRepository) -> None:
        self.session = session
        self.job_repo = job_repo

    async def _get_completed_summary(self, job_id: str) -> VideoSummary:
        job = await self.job_repo.get_by_id(job_id)
        if job is None:
            raise JobNotFoundError(f"Job {job_id!r} not found.")
        if job.status != "completed":
            raise SummaryNotReadyError(
                f"Job {job_id!r} is not completed (status={job.status!r})."
            )

        result = await self.session.execute(
            select(VideoSummary).where(VideoSummary.video_id == job.id)
        )
        summary_row = result.scalar_one_or_none()
        if summary_row is None:
            raise SummaryNotReadyError(f"Summary for job {job_id!r} not yet available.")
        return summary_row

    async def get_summary(self, job_id: str) -> SummaryResponse:
        row = await self._get_completed_summary(job_id)
        return SummaryResponse(
            job_id=row.video_id,
            summary=row.summary or "",
            model_used=row.model_used,
        )

    async def get_timeline(self, job_id: str) -> TimelineResponse:
        row = await self._get_completed_summary(job_id)
        events: list[TimelineEvent] = []
        if row.timeline:
            for item in row.timeline:
                events.append(
                    TimelineEvent(timestamp=item["timestamp"], event=item["event"])
                )
        return TimelineResponse(job_id=row.video_id, timeline=events)
