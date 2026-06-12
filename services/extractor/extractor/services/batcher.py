from extractor.core.config import get_settings
from extractor.domain.frame import FrameMetadata
from extractor.services import BaseService


class BatcherService(BaseService):
    def partition(self, frames: list[FrameMetadata]) -> list[list[FrameMetadata]]:
        settings = get_settings()
        batch_size = settings.BATCH_SIZE
        batches = [
            frames[i : i + batch_size] for i in range(0, len(frames), batch_size)
        ]
        return batches
