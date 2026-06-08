import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, select, update
from sqlalchemy.sql import func

from api.core.config import get_settings
from api.db.models import Frame, FrameAnalysis, Video
from api.repositories import BaseRepository


class JobRepository(BaseRepository):
    async def create(
        self,
        job_id: uuid.UUID,
        filename: str,
        file_size_bytes: int,
        duration_seconds: float,
        resolution: str,
        fps: float,
    ) -> Video:
        job = Video(
            id=job_id,
            filename=filename,
            status="queued",
            stage="upload_validation",
            file_size_bytes=file_size_bytes,
            duration_seconds=duration_seconds,
            resolution=resolution,
            fps=fps,
        )
        self.session.add(job)
        await self.session.flush()
        await self.session.refresh(job)
        return job

    async def get_by_id(self, job_id: str | uuid.UUID) -> Video | None:
        result = await self.session.execute(select(Video).where(Video.id == job_id))
        return result.scalar_one_or_none()

    async def update_status(
        self,
        job_id: str | uuid.UUID,
        status: str,
        stage: str,
        error_message: str | None = None,
    ) -> None:
        values: dict = {"status": status, "stage": stage}
        if error_message is not None:
            values["error_message"] = error_message
        await self.session.execute(
            update(Video).where(Video.id == job_id).values(**values)
        )

    async def update_progress(self, job_id: str | uuid.UUID, progress_pct: int) -> None:
        await self.session.execute(
            update(Video).where(Video.id == job_id).values(progress_pct=progress_pct)
        )

    async def mark_completed(self, job_id: str | uuid.UUID) -> None:
        settings = get_settings()
        now = datetime.now(tz=timezone.utc)
        expires_at = now + timedelta(days=settings.JOB_TTL_DAYS)
        await self.session.execute(
            update(Video)
            .where(Video.id == job_id)
            .values(
                status="completed",
                stage="completed",
                progress_pct=100,
                completed_at=now,
                expires_at=expires_at,
            )
        )

    async def mark_failed(
        self,
        job_id: str | uuid.UUID,
        stage: str,
        error_message: str,
        ttl_days: int,
    ) -> None:
        expires_at = datetime.now(tz=timezone.utc) + timedelta(days=ttl_days)
        await self.session.execute(
            update(Video)
            .where(Video.id == job_id)
            .values(
                status="failed",
                stage=stage,
                error_message=error_message,
                expires_at=expires_at,
            )
        )

    async def get_expired_jobs(self) -> list[Video]:
        result = await self.session.execute(
            select(Video).where(
                and_(
                    Video.expires_at < func.now(),
                    Video.cleaned_at.is_(None),
                    Video.status.in_(["completed", "failed"]),
                )
            )
        )
        return list(result.scalars().all())

    async def is_analysis_complete(self, job_id: str | uuid.UUID) -> bool:
        row = await self.session.execute(
            select(
                func.count(Frame.id).label("total"),
                func.count(FrameAnalysis.id).label("analyzed"),
            )
            .select_from(Frame)
            .outerjoin(FrameAnalysis, Frame.id == FrameAnalysis.frame_id)
            .where(Frame.video_id == job_id)
        )
        counts = row.one()
        return counts.total > 0 and counts.total == counts.analyzed

    async def mark_cleaned(self, job_id: str | uuid.UUID) -> None:
        await self.session.execute(
            update(Video).where(Video.id == job_id).values(cleaned_at=func.now())
        )
