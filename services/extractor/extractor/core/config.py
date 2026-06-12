from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    SCENE_THRESHOLD: float = 0.35
    FRAME_INTERVAL: int = 150
    BATCH_SIZE: int = 5
    DATA_ROOT: str = "/data"
    FFMPEG_BIN: str = "ffmpeg"
    FFPROBE_BIN: str = "ffprobe"
    MAX_DURATION_SEC: int = 600

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
