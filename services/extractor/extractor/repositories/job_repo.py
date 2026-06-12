from sqlalchemy import text

from extractor.repositories import BaseRepository


class JobRepository(BaseRepository):
    async def update_status(
        self,
        job_id: str,
        status: str,
        stage: str,
        error_message: str | None = None,
    ) -> None:
        query = text("""
            UPDATE videos
            SET status = :status, stage = :stage, error_message = :error_message
            WHERE id = :job_id
        """)
        await self.session.execute(
            query,
            {
                "job_id": job_id,
                "status": status,
                "stage": stage,
                "error_message": error_message,
            },
        )

    async def update_progress(self, job_id: str, progress_pct: int) -> None:
        query = text("""
            UPDATE videos
            SET progress_pct = :progress_pct
            WHERE id = :job_id
        """)
        await self.session.execute(
            query,
            {
                "job_id": job_id,
                "progress_pct": progress_pct,
            },
        )
