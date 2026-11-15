"""Her isteğe bir `request_id` atayan ve isteği loglayan middleware (Bölüm 4)."""

import time
from uuid import uuid4

import structlog
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import RequestResponseEndpoint

REQUEST_ID_HEADER = "X-Request-ID"

logger = structlog.get_logger(__name__)


def register_middleware(app: FastAPI) -> None:
    app.middleware("http")(_request_context)


async def _request_context(request: Request, call_next: RequestResponseEndpoint) -> Response:
    # İstemciden gelen kimliğe güvenilmez (log enjeksiyonu riski); her zaman yenisi üretilir.
    request_id = str(uuid4())
    request.state.request_id = request_id
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)

    started = time.perf_counter()
    response = await call_next(request)
    response.headers[REQUEST_ID_HEADER] = request_id
    logger.info(
        "request_completed",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration_ms=round((time.perf_counter() - started) * 1000, 1),
    )
    return response
