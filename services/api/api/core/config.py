from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    MAX_FILE_SIZE_MB: int = 500
    MAX_DURATION_SEC: int = 600
    DATA_ROOT: str = "/data"
    BATCH_SIZE: int = 5
    JOB_TTL_DAYS: int = 7
    FAILED_JOB_TTL_DAYS: int = 1

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
