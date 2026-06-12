from dataclasses import dataclass


@dataclass
class VideoMeta:
    duration_seconds: float
    fps: float
    width: int
    height: int
    codec: str
    total_frames: int


class DurationExceededError(ValueError):
    pass
