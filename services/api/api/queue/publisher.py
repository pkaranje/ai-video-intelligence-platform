import dramatiq

from shared.messages import ExtractionMessage


# Stub actor — real implementation lives in services/extractor.
# Declaring it here lets the API enqueue to the extraction queue without
# importing the extractor package.
@dramatiq.actor(queue_name="extraction")
def extraction_task(job_id: str) -> None:  # pragma: no cover
    raise NotImplementedError("This stub is never executed in the API process.")


def enqueue_extraction(job_id: str) -> None:
    msg = ExtractionMessage(job_id=job_id)
    extraction_task.send(job_id=msg.job_id)
