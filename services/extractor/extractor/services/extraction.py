import re
from pathlib import Path

from extractor.core.config import get_settings
from extractor.domain.video import VideoMeta
from extractor.repositories.ffmpeg_runner import FFmpegRunner
from extractor.services import BaseService


class ExtractionService(BaseService):
    def __init__(self, runner: FFmpegRunner | None = None) -> None:
        self.runner = runner or FFmpegRunner()

    async def run(
        self,
        video_path: str,
        job_id: str,
        video_meta: VideoMeta,
    ) -> list[tuple[int, str]]:
        settings = get_settings()
        output_dir = Path(settings.DATA_ROOT) / "frames" / job_id
        output_dir.mkdir(parents=True, exist_ok=True)

        exit_code, stderr = await self.runner.run(
            video_path=video_path,
            output_dir=str(output_dir),
            scene_threshold=settings.SCENE_THRESHOLD,
            frame_interval=settings.FRAME_INTERVAL,
        )

        frame_files = sorted(output_dir.glob("frame_*.jpg"))

        if exit_code != 0:
            if not frame_files:
                from extractor.domain.frame import FrameExtractionError

                raise FrameExtractionError(
                    f"FFmpeg failed (rc={exit_code}) and no frames were extracted. stderr: {stderr.strip()}"
                )
            self.logger.warning(
                "ffmpeg_nonzero_but_frames_exist",
                exit_code=exit_code,
                frame_count=len(frame_files),
            )

        raw_frames: list[tuple[int, str]] = []
        pattern = re.compile(r"frame_(\d+)\.jpg$")
        for path in frame_files:
            match = pattern.search(path.name)
            if match:
                frame_number = int(match.group(1))
                raw_frames.append((frame_number, str(path)))

        return sorted(raw_frames, key=lambda x: x[0])
