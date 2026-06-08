from enum import StrEnum

MAX_FILE_SIZE_MB = 500


class VideoStatus(StrEnum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class UploadTooLargeError(ValueError):
    pass


class UnsupportedFormatError(ValueError):
    pass


def validate_upload(filename: str, content_type: str, size_bytes: int) -> None:
    if content_type != "video/mp4":
        raise UnsupportedFormatError(f"Unsupported format: {content_type!r}. Only video/mp4 is accepted.")
    if size_bytes > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise UploadTooLargeError(f"File size {size_bytes} bytes exceeds limit of {MAX_FILE_SIZE_MB} MB.")
