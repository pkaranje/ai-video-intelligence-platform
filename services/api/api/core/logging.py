import time
import functools
from typing import Any, Callable

import structlog
from loguru import logger


def configure_logging() -> None:
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(20),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Route structlog output through loguru
    import logging

    class InterceptHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno
            frame, depth = logging.currentframe(), 2
            while frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back  # type: ignore[assignment]
                depth += 1
            logger.opt(depth=depth, exception=record.exc_info).log(
                level, record.getMessage()
            )

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)


class LoggerMixin:
    @property
    def logger(self) -> Any:
        return structlog.get_logger(self.__class__.__name__)


def log_call(func: Callable) -> Callable:
    @functools.wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        log = structlog.get_logger(func.__qualname__)
        log.info("call_start", func=func.__name__)
        start = time.monotonic()
        try:
            result = await func(*args, **kwargs)
            log.info(
                "call_end",
                func=func.__name__,
                elapsed_ms=round((time.monotonic() - start) * 1000, 2),
            )
            return result
        except Exception as exc:
            log.error(
                "call_error",
                func=func.__name__,
                elapsed_ms=round((time.monotonic() - start) * 1000, 2),
                error=str(exc),
            )
            raise

    @functools.wraps(func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        log = structlog.get_logger(func.__qualname__)
        log.info("call_start", func=func.__name__)
        start = time.monotonic()
        try:
            result = func(*args, **kwargs)
            log.info(
                "call_end",
                func=func.__name__,
                elapsed_ms=round((time.monotonic() - start) * 1000, 2),
            )
            return result
        except Exception as exc:
            log.error(
                "call_error",
                func=func.__name__,
                elapsed_ms=round((time.monotonic() - start) * 1000, 2),
                error=str(exc),
            )
            raise

    import asyncio

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper
