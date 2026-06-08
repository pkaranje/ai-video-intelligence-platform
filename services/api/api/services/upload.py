import asyncio
import uuid
from pathlib import Path

from fastapi import UploadFile

from api.core.config import get_settings
from api.domain.video import DurationExceededError, validate_upload
from api.queue.publisher import enqueue_extraction
from api.repositories.ffprobe_client import FFprobeClient
from api.repositories.job_repo import JobRepository
from api.schemas.video import JobStatus, UploadResponse
from api.services import BaseService


class UploadService(BaseService):
    def __init__(
        self, job_repo: JobRepository, ffprobe: FFprobeClient | None = None
    ) -> None:
        self.job_repo = job_repo
        self.ffprobe = ffprobe or FFprobeClient()

    async def upload(self, file: UploadFile) -> UploadResponse:
        settings = get_settings()

        content = await file.read()
        validate_upload(
            filename=file.filename or "",
            content_type=file.content_type or "",
            size_bytes=len(content),
            max_file_size_mb=settings.MAX_FILE_SIZE_MB,
        )

        job_id = uuid.uuid4()
        uploads_dir = Path(settings.DATA_ROOT) / "uploads"
        uploads_dir.mkdir(parents=True, exist_ok=True)
        dest = uploads_dir / f"{job_id}.mp4"

        def _write(path: Path, data: bytes) -> None:
            path.write_bytes(data)

        await asyncio.to_thread(_write, dest, content)

        try:
            probe = await self.ffprobe.probe(str(dest))
        except Exception:
            await asyncio.to_thread(dest.unlink, True)
            raise

        if probe.duration_seconds > settings.MAX_DURATION_SEC:
            await asyncio.to_thread(dest.unlink, True)
            raise DurationExceededError(
                f"Video duration {probe.duration_seconds:.1f}s exceeds limit of {settings.MAX_DURATION_SEC}s."
            )

        resolution = f"{probe.width}x{probe.height}"
        job = await self.job_repo.create(
            job_id=job_id,
            filename=file.filename or dest.name,
            file_size_bytes=len(content),
            duration_seconds=probe.duration_seconds,
            resolution=resolution,
            fps=probe.fps,
        )

        enqueue_extraction(str(job.id))

        return UploadResponse(
            job_id=job.id,
            status=JobStatus.queued,
            message="Upload accepted. Processing started.",
        )
