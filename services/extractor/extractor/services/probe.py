from extractor.core.config import get_settings
from extractor.domain.video import DurationExceededError, VideoMeta
from extractor.repositories.ffprobe_client import FFprobeClient
from extractor.services import BaseService


class ProbeService(BaseService):
    def __init__(self, ffprobe: FFprobeClient | None = None) -> None:
        self.ffprobe = ffprobe or FFprobeClient()

    async def run(self, video_path: str) -> VideoMeta:
        settings = get_settings()
        meta = await self.ffprobe.probe(video_path)
        if meta.duration_seconds > settings.MAX_DURATION_SEC:
            raise DurationExceededError(
                f"Video duration {meta.duration_seconds:.1f}s exceeds limit of {settings.MAX_DURATION_SEC}s."
            )
        return meta
