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


class DurationExceededError(ValueError):
    pass


class JobNotFoundError(LookupError):
    pass


class SummaryNotReadyError(LookupError):
    pass


def validate_upload(
    filename: str,
    content_type: str,
    size_bytes: int,
    max_file_size_mb: int = MAX_FILE_SIZE_MB,
) -> None:
    if content_type != "video/mp4":
        raise UnsupportedFormatError(
            f"Unsupported format: {content_type!r}. Only video/mp4 is accepted."
        )
    if size_bytes > max_file_size_mb * 1024 * 1024:
        raise UploadTooLargeError(
            f"File size {size_bytes} bytes exceeds limit of {max_file_size_mb} MB."
        )
