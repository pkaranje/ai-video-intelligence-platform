from api.domain.video import JobNotFoundError
from api.repositories.job_repo import JobRepository
from api.schemas.video import JobStatus, ProgressStage, StatusResponse
from api.services import BaseService


class StatusService(BaseService):
    def __init__(self, job_repo: JobRepository) -> None:
        self.job_repo = job_repo

    async def get(self, job_id: str) -> StatusResponse:
        job = await self.job_repo.get_by_id(job_id)
        if job is None:
            raise JobNotFoundError(f"Job {job_id!r} not found.")

        stage: ProgressStage | None = None
        if job.stage is not None:
            try:
                stage = ProgressStage(job.stage)
            except ValueError:
                stage = None

        return StatusResponse(
            job_id=job.id,
            status=JobStatus(job.status),
            stage=stage,
            progress_pct=job.progress_pct,
            error_message=job.error_message,
        )
