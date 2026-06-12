import dramatiq
from dramatiq.brokers.redis import RedisBroker

from extractor.core.config import get_settings
from shared.messages import AnalysisBatchMessage


def _ensure_broker() -> None:
    try:
        dramatiq.get_broker()
    except Exception:
        dramatiq.set_broker(RedisBroker(url=get_settings().REDIS_URL))


_ensure_broker()


@dramatiq.actor(queue_name="analysis")
def analysis_batch_task(job_id: str, frame_ids: list[str]) -> None:  # pragma: no cover
    raise NotImplementedError("Stub — consumed by worker service.")


def enqueue_analysis_batch(job_id: str, frame_ids: list[str]) -> None:
    msg = AnalysisBatchMessage(job_id=job_id, frame_ids=frame_ids)
    analysis_batch_task.send(msg.job_id, msg.frame_ids)
