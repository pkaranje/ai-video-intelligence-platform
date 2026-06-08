import pytest

from api.domain.frame import FrameValidationError, validate_frame_metadata

_VALID = {
    "video_id": "vid-1",
    "frame_id": "frm-1",
    "frame_path": "/data/frames/vid-1/0001.jpg",
    "timestamp": 1.5,
    "frame_number": 1,
    "selection_reason": "periodic",
}


def test_validate_frame_metadata_happy_path():
    validate_frame_metadata(_VALID)


@pytest.mark.parametrize(
    "missing_key",
    ["video_id", "frame_id", "frame_path", "timestamp", "frame_number", "selection_reason"],
)
def test_validate_frame_metadata_missing_key(missing_key):
    metadata = {k: v for k, v in _VALID.items() if k != missing_key}
    with pytest.raises(FrameValidationError):
        validate_frame_metadata(metadata)
