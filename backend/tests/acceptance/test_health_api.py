from uuid import UUID

from fastapi import FastAPI
from fastapi.testclient import TestClient

from kovan.api.deps import get_readiness_service
from kovan.application.health import ReadinessService
from tests.fakes import FakeProbe


def _use_probes(app: FastAPI, *probes: FakeProbe) -> None:
    app.dependency_overrides[get_readiness_service] = lambda: ReadinessService(probes)


def test_health_returns_ok_with_request_id(client: TestClient) -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    UUID(response.headers["X-Request-ID"])  # geçerli bir UUID olmalı


def test_each_request_gets_its_own_request_id(client: TestClient) -> None:
    first = client.get("/api/v1/health").headers["X-Request-ID"]
    second = client.get("/api/v1/health").headers["X-Request-ID"]

    assert first != second


def test_ready_returns_200_when_dependencies_are_up(app: FastAPI, client: TestClient) -> None:
    _use_probes(app, FakeProbe("database", ready=True))

    response = client.get("/api/v1/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "checks": {"database": "up"}}


def test_ready_returns_503_when_a_dependency_is_down(app: FastAPI, client: TestClient) -> None:
    _use_probes(app, FakeProbe("database", ready=False))

    response = client.get("/api/v1/health/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "not_ready", "checks": {"database": "down"}}


def test_ready_with_real_probe_reports_unreachable_database_as_down(client: TestClient) -> None:
    response = client.get("/api/v1/health/ready")

    assert response.status_code == 503
    assert response.json()["checks"] == {"database": "down"}
