import logging
from time import perf_counter
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Record one structured log event for every HTTP request."""

    def __init__(self, app: ASGIApp, logger: logging.Logger) -> None:
        super().__init__(app)
        self.logger = logger

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        started_at = perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round(
                (perf_counter() - started_at) * 1000,
                2,
            )
            self.logger.exception(
                "HTTP request failed",
                extra={
                    "event": "http_request_failed",
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": 500,
                    "duration_ms": duration_ms,
                },
            )
            raise

        duration_ms = round(
            (perf_counter() - started_at) * 1000,
            2,
        )
        response.headers["X-Request-ID"] = request_id

        self.logger.info(
            "HTTP request completed",
            extra={
                "event": "http_request_completed",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )

        return response
