import asyncio

from extractor.core.logging import LoggerMixin


class FFmpegRunner(LoggerMixin):
    async def run(
        self,
        video_path: str,
        output_dir: str,
        scene_threshold: float,
        frame_interval: int,
    ) -> tuple[int, str]:
        filter_str = (
            f"select='gt(scene,{scene_threshold})+not(mod(n,{frame_interval}))'"
        )
        cmd = [
            "ffmpeg",
            "-i",
            video_path,
            "-vf",
            filter_str,
            "-vsync",
            "vfr",
            "-q:v",
            "4",
            f"{output_dir}/frame_%04d.jpg",
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        return proc.returncode, stderr.decode()
