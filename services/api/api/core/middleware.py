import time
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())
        start = time.monotonic()

        with structlog.contextvars.bound_contextvars(request_id=request_id):
            response = await call_next(request)
            structlog.get_logger().info(
                "request_completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=round((time.monotonic() - start) * 1000, 2),
            )

        response.headers["X-Request-ID"] = request_id
        return response
