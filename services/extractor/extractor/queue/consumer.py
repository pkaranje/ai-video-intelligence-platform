import asyncio

import dramatiq
from dramatiq.brokers.redis import RedisBroker
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from extractor.core.config import get_settings
from extractor.core.logging import LoggerMixin
from shared.middleware import ActorMetricsMiddleware

_log = LoggerMixin()

settings = get_settings()

broker = RedisBroker(url=settings.REDIS_URL)
dramatiq.set_broker(broker)
broker.add_middleware(ActorMetricsMiddleware())

# Module-level session factory — initialised in main.py before workers start.
_session_factory: async_sessionmaker[AsyncSession] | None = None


def set_session_factory(factory: async_sessionmaker[AsyncSession]) -> None:
    global _session_factory
    _session_factory = factory


@dramatiq.actor(queue_name="extraction", max_retries=3)
def extraction_task(job_id: str) -> None:
    asyncio.run(_run_extraction(job_id))


async def _run_extraction(job_id: str) -> None:
    from extractor.pipeline.orchestrator import ExtractionOrchestrator
    from extractor.repositories.job_repo import JobRepository

    if _session_factory is None:
        raise RuntimeError(
            "Session factory not initialised — call set_session_factory() in main.py"
        )

    try:
        async with _session_factory.begin() as session:
            await ExtractionOrchestrator(session).run(job_id)
    except Exception as exc:
        async with _session_factory.begin() as session:
            await JobRepository(session).update_status(
                job_id=job_id,
                status="failed",
                stage="frame_extraction",
                error_message=str(exc),
            )
        raise
