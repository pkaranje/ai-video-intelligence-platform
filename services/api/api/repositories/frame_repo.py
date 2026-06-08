import uuid

from sqlalchemy import select

from api.db.models import Frame, FrameAnalysis
from api.repositories import BaseRepository


class FrameRepository(BaseRepository):
    async def bulk_insert_frames(self, frames: list[dict]) -> list[str]:
        objects = [
            Frame(
                id=uuid.uuid4(),
                video_id=f["video_id"],
                frame_path=f["frame_path"],
                timestamp=f["timestamp"],
                frame_number=f["frame_number"],
                selection_reason=f["selection_reason"],
                scene_score=f.get("scene_score"),
            )
            for f in frames
        ]
        self.session.add_all(objects)
        await self.session.flush()
        return [str(obj.id) for obj in objects]

    async def get_frames_for_job(self, job_id: str | uuid.UUID) -> list[Frame]:
        result = await self.session.execute(
            select(Frame)
            .where(Frame.video_id == job_id)
            .order_by(Frame.timestamp.asc())
        )
        return list(result.scalars().all())

    async def get_descriptions_for_job(self, job_id: str | uuid.UUID) -> list[dict]:
        result = await self.session.execute(
            select(Frame.timestamp, FrameAnalysis.description)
            .join(FrameAnalysis, Frame.id == FrameAnalysis.frame_id)
            .where(Frame.video_id == job_id)
            .order_by(Frame.timestamp.asc())
        )
        return [
            {"timestamp": row.timestamp, "description": row.description}
            for row in result
        ]
