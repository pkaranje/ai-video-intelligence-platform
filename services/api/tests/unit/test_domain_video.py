import pytest

from api.domain.video import (
    MAX_FILE_SIZE_MB,
    UnsupportedFormatError,
    UploadTooLargeError,
    validate_upload,
)


def test_validate_upload_happy_path():
    validate_upload("clip.mp4", "video/mp4", 1024 * 1024)


def test_validate_upload_wrong_content_type():
    with pytest.raises(UnsupportedFormatError):
        validate_upload("clip.avi", "video/avi", 1024 * 1024)


def test_validate_upload_too_large():
    over_limit = MAX_FILE_SIZE_MB * 1024 * 1024 + 1
    with pytest.raises(UploadTooLargeError):
        validate_upload("clip.mp4", "video/mp4", over_limit)


def test_validate_upload_exactly_at_limit():
    at_limit = MAX_FILE_SIZE_MB * 1024 * 1024
    validate_upload("clip.mp4", "video/mp4", at_limit)
