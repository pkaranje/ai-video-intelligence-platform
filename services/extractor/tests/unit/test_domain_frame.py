import pytest
from datetime import datetime
from uuid import uuid4

from extractor.domain.frame import (
    SelectionReason,
    FrameMetadata,
    FrameExtractionError,
)


class TestFrameMetadata:
    def test_frame_metadata_creation_all_fields(self):
        video_id = uuid4()
        frame_id = "frame_001"
        frame_path = "/data/frames/job_123/frame_001.jpg"
        timestamp = 1.5
        frame_number = 1
        selection_reason = SelectionReason.periodic
        scene_score = 0.85
        created_at = datetime.now()

        metadata = FrameMetadata(
            video_id=video_id,
            frame_id=frame_id,
            frame_path=frame_path,
            timestamp=timestamp,
            frame_number=frame_number,
            selection_reason=selection_reason,
            scene_score=scene_score,
            created_at=created_at,
        )

        assert metadata.video_id == video_id
        assert metadata.frame_id == frame_id
        assert metadata.frame_path == frame_path
        assert metadata.timestamp == timestamp
        assert metadata.frame_number == frame_number
        assert metadata.selection_reason == SelectionReason.periodic
        assert metadata.scene_score == scene_score
        assert metadata.created_at == created_at

    def test_frame_metadata_with_none_scene_score(self):
        video_id = uuid4()
        metadata = FrameMetadata(
            video_id=video_id,
            frame_id="frame_001",
            frame_path="/data/frames/frame_001.jpg",
            timestamp=1.5,
            frame_number=1,
            selection_reason=SelectionReason.scene_change,
            scene_score=None,
            created_at=datetime.now(),
        )

        assert metadata.scene_score is None


class TestSelectionReason:
    def test_selection_reason_scene_change(self):
        assert SelectionReason.scene_change.value == "scene_change"

    def test_selection_reason_periodic(self):
        assert SelectionReason.periodic.value == "periodic"

    def test_selection_reason_both(self):
        assert SelectionReason.both.value == "both"

    def test_selection_reason_enum_members(self):
        reasons = list(SelectionReason)
        assert len(reasons) == 3
        assert SelectionReason.scene_change in reasons
        assert SelectionReason.periodic in reasons
        assert SelectionReason.both in reasons


class TestFrameExtractionError:
    def test_frame_extraction_error_creation(self):
        error_msg = "Failed to extract frame"
        error = FrameExtractionError(error_msg)
        assert str(error) == error_msg

    def test_frame_extraction_error_is_exception(self):
        assert issubclass(FrameExtractionError, Exception)
