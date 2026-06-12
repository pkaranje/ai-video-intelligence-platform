from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID


class SelectionReason(str, Enum):
    scene_change = "scene_change"
    periodic = "periodic"
    both = "both"


@dataclass
class FrameMetadata:
    video_id: UUID
    frame_id: str
    frame_path: str
    timestamp: float
    frame_number: int
    selection_reason: SelectionReason
    scene_score: float | None
    created_at: datetime


class FrameExtractionError(Exception):
    pass
