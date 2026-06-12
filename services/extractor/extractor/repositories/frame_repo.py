from sqlalchemy import text

from extractor.domain.frame import FrameMetadata
from extractor.repositories import BaseRepository


class FrameRepository(BaseRepository):
    async def bulk_insert_frames(self, frames: list[FrameMetadata]) -> list[str]:
        if not frames:
            return []

        result_ids = []
        for frame in frames:
            query = text("""
                INSERT INTO frames (id, video_id, frame_path, timestamp, frame_number, selection_reason, scene_score)
                VALUES (:frame_id, :video_id, :frame_path, :timestamp, :frame_number, :selection_reason, :scene_score)
                RETURNING id
            """)
            row = await self.session.execute(
                query,
                {
                    "frame_id": str(frame.frame_id),
                    "video_id": str(frame.video_id),
                    "frame_path": frame.frame_path,
                    "timestamp": frame.timestamp,
                    "frame_number": frame.frame_number,
                    "selection_reason": frame.selection_reason.value,
                    "scene_score": frame.scene_score,
                },
            )
            frame_id = row.scalar_one()
            result_ids.append(str(frame_id))

        return result_ids
