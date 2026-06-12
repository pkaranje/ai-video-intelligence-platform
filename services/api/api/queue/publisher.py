import dramatiq
from dramatiq.brokers.redis import RedisBroker
from loguru import logger

from api.core.config import get_settings
from shared.messages import ExtractionMessage


def _configure_broker() -> None:
    broker = RedisBroker(url=get_settings().REDIS_URL)
    dramatiq.set_broker(broker)


_configure_broker()


# Stub actor — declared here so the API can enqueue without importing extractor.
# Real implementation lives in services/extractor/extractor/queue/consumer.py.
@dramatiq.actor(queue_name="extraction")
def extraction_task(job_id: str) -> None:  # pragma: no cover
    raise NotImplementedError("Stub — never executed in the API process.")


def enqueue_extraction(job_id: str) -> None:
    msg = ExtractionMessage(job_id=job_id)
    logger.info("extraction_enqueued", job_id=msg.job_id)
    extraction_task.send(job_id=msg.job_id)
