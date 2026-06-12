from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from extractor.core.config import get_settings
from extractor.core.logging import configure_logging

configure_logging()

settings = get_settings()

_engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
_session_factory = async_sessionmaker(_engine, expire_on_commit=False)

# Register the session factory before Dramatiq forks workers.
from extractor.queue.consumer import extraction_task, set_session_factory  # noqa: E402

set_session_factory(_session_factory)

__all__ = ["extraction_task"]
