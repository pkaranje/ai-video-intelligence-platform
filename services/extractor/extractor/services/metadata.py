import uuid
from datetime import datetime, timezone

from extractor.core.config import get_settings
from extractor.domain.frame import FrameMetadata, SelectionReason
from extractor.domain.video import VideoMeta
from extractor.services import BaseService


class MetadataService(BaseService):
    def resolve(
        self,
        raw_frames: list[tuple[int, str]],
        video_meta: VideoMeta,
        video_id: str,
    ) -> list[FrameMetadata]:
        settings = get_settings()
        frames: list[FrameMetadata] = []
        now = datetime.now(tz=timezone.utc)

        for frame_number, frame_path in raw_frames:
            timestamp = frame_number / video_meta.fps if video_meta.fps else 0.0
            is_periodic = frame_number % settings.FRAME_INTERVAL == 0
            # scene change is any frame not selected by periodic interval alone;
            # ffmpeg select filter outputs frames matching either condition
            is_scene = not is_periodic

            if is_periodic and is_scene:
                reason = SelectionReason.both
            elif is_periodic:
                reason = SelectionReason.periodic
            else:
                reason = SelectionReason.scene_change

            frames.append(
                FrameMetadata(
                    video_id=uuid.UUID(video_id),
                    frame_id=str(uuid.uuid4()),
                    frame_path=frame_path,
                    timestamp=round(timestamp, 4),
                    frame_number=frame_number,
                    selection_reason=reason,
                    scene_score=None,
                    created_at=now,
                )
            )

        return frames
