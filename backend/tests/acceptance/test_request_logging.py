"""Her istek (hata verenler dahil) yöntem, yol, durum ve süreyle loglanır."""

from collections.abc import MutableMapping
from typing import Any

from fastapi import APIRouter
from fastapi.testclient import TestClient
from structlog.testing import capture_logs

from kovan.main import create_app
from tests.fakes import make_test_settings

_failing_router = APIRouter(prefix="/_test")


@_failing_router.get("/bug")
def _bug() -> None:
    raise RuntimeError("beklenmeyen hata")


def _completed_requests(path: str) -> list[MutableMapping[str, Any]]:
    app = create_app(make_test_settings(log_level="INFO"))
    app.include_router(_failing_router)
    with TestClient(app, raise_server_exceptions=False) as client, capture_logs() as logs:
        client.get(path)
    return [entry for entry in logs if entry["event"] == "request_completed"]


def test_successful_request_is_logged() -> None:
    [entry] = _completed_requests("/api/v1/health")

    assert (entry["method"], entry["path"], entry["status"]) == ("GET", "/api/v1/health", 200)
    assert "duration_ms" in entry


def test_failed_request_is_logged_as_500() -> None:
    [entry] = _completed_requests("/_test/bug")

    assert (entry["path"], entry["status"]) == ("/_test/bug", 500)
    assert "duration_ms" in entry
