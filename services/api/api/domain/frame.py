from enum import StrEnum

_REQUIRED_KEYS = {
    "video_id",
    "frame_id",
    "frame_path",
    "timestamp",
    "frame_number",
    "selection_reason",
}


class SelectionReason(StrEnum):
    scene_change = "scene_change"
    periodic = "periodic"
    both = "both"


class FrameValidationError(ValueError):
    pass


def validate_frame_metadata(metadata: dict) -> None:
    missing = _REQUIRED_KEYS - metadata.keys()
    if missing:
        raise FrameValidationError(
            f"Frame metadata missing required keys: {sorted(missing)}"
        )
