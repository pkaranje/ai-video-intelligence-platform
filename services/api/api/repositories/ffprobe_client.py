import asyncio
import json
from dataclasses import dataclass

from api.core.logging import LoggerMixin


class FFprobeError(Exception):
    pass


@dataclass
class FFprobeResult:
    duration_seconds: float
    fps: float
    width: int
    height: int
    codec: str


def _parse_fps(fps_str: str) -> float:
    try:
        num, den = fps_str.split("/")
        d = float(den)
        return float(num) / d if d else 0.0
    except (ValueError, ZeroDivisionError):
        return 0.0


class FFprobeClient(LoggerMixin):
    async def probe(self, video_path: str) -> FFprobeResult:
        cmd = [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            video_path,
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise FFprobeError(
                f"ffprobe failed (rc={proc.returncode}): {stderr.decode().strip()}"
            )

        try:
            data = json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise FFprobeError(f"ffprobe output is not valid JSON: {exc}") from exc

        fmt = data.get("format", {})
        streams = data.get("streams", [])
        video_stream = next(
            (s for s in streams if s.get("codec_type") == "video"), None
        )
        if video_stream is None:
            raise FFprobeError("No video stream found in file.")

        return FFprobeResult(
            duration_seconds=float(fmt.get("duration", 0)),
            fps=_parse_fps(video_stream.get("avg_frame_rate", "0/1")),
            width=int(video_stream.get("width", 0)),
            height=int(video_stream.get("height", 0)),
            codec=video_stream.get("codec_name", ""),
        )
