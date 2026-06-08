import time

import dramatiq
from loguru import logger


class ActorMetricsMiddleware(dramatiq.Middleware):
    def before_process_message(self, broker, message):
        message.options["started_at"] = time.monotonic()

    def after_process_message(self, broker, message, *, result=None, exception=None):
        duration_ms = round((time.monotonic() - message.options["started_at"]) * 1000, 2)
        logger.info(
            "actor_completed",
            actor=message.actor_name,
            queue=message.queue_name,
            duration_ms=duration_ms,
            status="failed" if exception else "success",
            job_id=message.kwargs.get("job_id"),
            retries=message.options.get("retries", 0),
        )
