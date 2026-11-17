"""Tüm hataların aynı JSON formatında döndüğünü doğrular (docs/api-contract.md "Hata formatı")."""

from typing import Any

import pytest
from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.testclient import TestClient

from kovan.application.errors import ApplicationError, AuthenticationError, ExternalServiceError
from kovan.domain.errors import ConflictError, DomainRuleError, NotFoundError

SECRET_DETAIL = "gizli-ic-detay-SELECT-sifre"


# Hata fırlatan, yalnızca testlerde kullanılan uç noktalar.
_test_router = APIRouter(prefix="/_test")


@_test_router.get("/rule")
def _rule() -> None:
    raise DomainRuleError("R-05", "Döngü oluşur.", code="PAGE_MOVE_CYCLE")


@_test_router.get("/not-found")
def _not_found() -> None:
    raise NotFoundError("Sayfa bulunamadı.", code="PAGE_NOT_FOUND")


@_test_router.get("/conflict")
def _conflict() -> None:
    raise ConflictError("Sürüm çakışması.", code="VERSION_CONFLICT", rule_code="R-07")


@_test_router.get("/auth")
def _auth() -> None:
    raise AuthenticationError("Oturum gerekli.")


@_test_router.get("/external")
def _external() -> None:
    raise ExternalServiceError("Servis kapalı.", code="AI_SERVICE_UNAVAILABLE")


@_test_router.get("/bug")
def _bug() -> None:
    raise RuntimeError(SECRET_DETAIL)


@_test_router.get("/unmapped")
def _unmapped() -> None:
    raise ApplicationError(SECRET_DETAIL, code="UNMAPPED")


@_test_router.get("/http-server-error/{status}")
def _http_server_error(status: int) -> None:
    raise HTTPException(status_code=status, detail=SECRET_DETAIL)


@_test_router.get("/validation")
def _validation(limit: int) -> dict[str, int]:
    return {"limit": limit}


@pytest.fixture
def error_client(app: FastAPI, client: TestClient) -> TestClient:
    app.include_router(_test_router)
    return client


def _error_of(response: Any) -> dict[str, Any]:
    error: dict[str, Any] = response.json()["error"]
    assert error["request_id"] == response.headers["X-Request-ID"]
    return error


@pytest.mark.parametrize(
    ("path", "status", "code", "rule"),
    [
        ("/_test/rule", 422, "PAGE_MOVE_CYCLE", "R-05"),
        ("/_test/not-found", 404, "PAGE_NOT_FOUND", None),
        ("/_test/conflict", 409, "VERSION_CONFLICT", "R-07"),
        ("/_test/auth", 401, "UNAUTHENTICATED", None),
        ("/_test/external", 503, "AI_SERVICE_UNAVAILABLE", None),
    ],
)
def test_known_errors_are_mapped_to_status_and_common_format(
    error_client: TestClient, path: str, status: int, code: str, rule: str | None
) -> None:
    response = error_client.get(path)

    assert response.status_code == status
    error = _error_of(response)
    assert error["code"] == code
    assert error["rule"] == rule
    assert error["message"]


def test_unexpected_error_returns_500_without_leaking_details(error_client: TestClient) -> None:
    response = error_client.get("/_test/bug")

    assert response.status_code == 500
    assert _error_of(response)["code"] == "INTERNAL_ERROR"
    assert SECRET_DETAIL not in response.text


def test_error_type_without_status_mapping_is_treated_as_internal_error(
    error_client: TestClient,
) -> None:
    response = error_client.get("/_test/unmapped")

    assert response.status_code == 500
    assert _error_of(response)["code"] == "INTERNAL_ERROR"
    assert SECRET_DETAIL not in response.text


@pytest.mark.parametrize("status", [500, 503])
def test_http_exception_with_server_status_does_not_leak_detail(
    error_client: TestClient, status: int
) -> None:
    response = error_client.get(f"/_test/http-server-error/{status}")

    assert response.status_code == 500
    assert _error_of(response)["code"] == "INTERNAL_ERROR"
    assert SECRET_DETAIL not in response.text


def test_validation_error_names_the_invalid_field(error_client: TestClient) -> None:
    response = error_client.get("/_test/validation", params={"limit": "çok"})

    assert response.status_code == 422
    error = _error_of(response)
    assert error["code"] == "VALIDATION_ERROR"
    assert [detail["field"] for detail in error["details"]] == ["query.limit"]
    assert "çok" not in response.text  # girilen değer yanıta konmaz


def test_unknown_route_uses_common_format(client: TestClient) -> None:
    response = client.get("/api/v1/olmayan-adres")

    assert response.status_code == 404
    assert _error_of(response)["code"] == "NOT_FOUND"


def test_wrong_http_method_returns_405_with_allow_header(client: TestClient) -> None:
    response = client.post("/api/v1/health")

    assert response.status_code == 405
    assert _error_of(response)["code"] == "METHOD_NOT_ALLOWED"
    assert response.headers["Allow"] == "GET"
