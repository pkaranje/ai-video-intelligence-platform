from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from extractor.core.config import get_settings
from extractor.core.logging import LoggerMixin
from extractor.queue.publisher import enqueue_analysis_batch
from extractor.repositories.frame_repo import FrameRepository
from extractor.repositories.job_repo import JobRepository
from extractor.services.batcher import BatcherService
from extractor.services.extraction import ExtractionService
from extractor.services.metadata import MetadataService
from extractor.services.probe import ProbeService


class ExtractionOrchestrator(LoggerMixin):
    def __init__(self, session: AsyncSession) -> None:
        self.job_repo = JobRepository(session)
        self.frame_repo = FrameRepository(session)
        self.probe = ProbeService()
        self.extraction = ExtractionService()
        self.metadata = MetadataService()
        self.batcher = BatcherService()

    async def run(self, job_id: str) -> None:
        settings = get_settings()
        video_path = str(Path(settings.DATA_ROOT) / "uploads" / f"{job_id}.mp4")

        await self.job_repo.update_status(
            job_id=job_id,
            status="running",
            stage="frame_extraction",
        )

        video_meta = await self.probe.run(video_path)

        raw_frames = await self.extraction.run(
            video_path=video_path,
            job_id=job_id,
            video_meta=video_meta,
        )

        frames = self.metadata.resolve(
            raw_frames=raw_frames,
            video_meta=video_meta,
            video_id=job_id,
        )

        await self.frame_repo.bulk_insert_frames(frames)

        batches = self.batcher.partition(frames)

        for batch in batches:
            batch_frame_ids = [f.frame_id for f in batch]
            enqueue_analysis_batch(job_id=job_id, frame_ids=batch_frame_ids)

        await self.job_repo.update_status(
            job_id=job_id,
            status="running",
            stage="ai_analysis",
        )
