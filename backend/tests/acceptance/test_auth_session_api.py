"""Giriş, çıkış ve /auth/me kabul testleri (US-02, ADR-008)."""

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from kovan.api.deps import get_auth_service
from kovan.application.auth_service import SESSION_LIFETIME, AuthService
from kovan.infrastructure.security.argon2 import Argon2PasswordHasher
from kovan.infrastructure.security.jwt import JwtTokenService
from kovan.main import create_app
from tests.fakes import TEST_JWT_SECRET, InMemoryUserRepository, make_test_settings

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
LOGOUT_URL = "/api/v1/auth/logout"
ME_URL = "/api/v1/auth/me"
COOKIE_NAME = "kovan_session"
EMAIL = "ayse@ornek.com"
PASSWORD = "gizli-sifre"
REGISTER_BODY = {"email": EMAIL, "password": PASSWORD, "display_name": "Ayşe Y."}
LOGIN_BODY = {"email": EMAIL, "password": PASSWORD}


@pytest.fixture
def auth_client(app: FastAPI, client: TestClient) -> TestClient:
    """Gerçek Argon2 ve JWT, bellekteki kullanıcı deposu: Docker gerekmez."""
    tokens = JwtTokenService(TEST_JWT_SECRET, SESSION_LIFETIME)
    service = AuthService(InMemoryUserRepository(), Argon2PasswordHasher(), tokens)
    app.dependency_overrides[get_auth_service] = lambda: service
    client.post(REGISTER_URL, json=REGISTER_BODY)
    return client


@pytest.fixture
def db_client(clean_users: Engine, postgres_url: str) -> Iterator[TestClient]:
    """Gerçek PostgreSQL'e bağlı uygulama (Testcontainers)."""
    app = create_app(make_test_settings(database_url=postgres_url))
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


@pytest.mark.ac("AC-02.1")
def test_login_sets_httponly_samesite_strict_cookie(auth_client: TestClient) -> None:
    response = auth_client.post(LOGIN_URL, json=LOGIN_BODY)

    assert response.status_code == 204
    cookie = response.headers["set-cookie"]
    assert cookie.startswith(f"{COOKIE_NAME}=")
    assert "HttpOnly" in cookie
    assert "SameSite=strict" in cookie
    assert "Path=/api" in cookie
    assert f"Max-Age={8 * 60 * 60}" in cookie


@pytest.mark.ac("AC-02.1")
def test_after_login_me_returns_current_user_without_password(auth_client: TestClient) -> None:
    auth_client.post(LOGIN_URL, json={**LOGIN_BODY, "email": "Ayse@Ornek.com"})

    response = auth_client.get(ME_URL)

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"id", "email", "display_name", "created_at"}
    assert body["email"] == EMAIL
    assert PASSWORD not in response.text


@pytest.mark.ac("AC-02.2")
@pytest.mark.parametrize(
    "body",
    [{**LOGIN_BODY, "password": "yanlis-sifre"}, {**LOGIN_BODY, "email": "yok@ornek.com"}],
    ids=["yanlis-sifre", "kayitsiz-eposta"],
)
def test_login_with_wrong_password_returns_generic_401(
    auth_client: TestClient, body: dict[str, str]
) -> None:
    response = auth_client.post(LOGIN_URL, json=body)

    assert response.status_code == 401
    error = response.json()["error"]
    assert error["code"] == "INVALID_CREDENTIALS"
    assert error["message"] == "E-posta veya şifre hatalı."
    assert "set-cookie" not in response.headers


@pytest.mark.ac("AC-02.3")
def test_logout_clears_cookie_and_blocks_access(auth_client: TestClient) -> None:
    auth_client.post(LOGIN_URL, json=LOGIN_BODY)

    response = auth_client.post(LOGOUT_URL)

    assert response.status_code == 204
    cookie = response.headers["set-cookie"]
    assert cookie.startswith(f'{COOKIE_NAME}=""') or cookie.startswith(f"{COOKIE_NAME}=;")
    assert "Max-Age=0" in cookie
    assert "Path=/api" in cookie
    assert auth_client.get(ME_URL).status_code == 401


@pytest.mark.ac("AC-02.4")
def test_protected_endpoint_without_session_returns_401(auth_client: TestClient) -> None:
    response = auth_client.get(ME_URL)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


@pytest.mark.ac("AC-02.4")
@pytest.mark.parametrize("expired", [True, False], ids=["suresi-dolmus", "bozuk"])
def test_protected_endpoint_with_expired_or_broken_session_returns_401(
    auth_client: TestClient, expired: bool
) -> None:
    nine_hours_ago = datetime.now(UTC) - timedelta(hours=9)
    old_tokens = JwtTokenService(TEST_JWT_SECRET, SESSION_LIFETIME, clock=lambda: nine_hours_ago)
    token = old_tokens.issue(uuid4()) if expired else "bozuk-token"
    auth_client.cookies.set(COOKIE_NAME, token, path="/api")

    response = auth_client.get(ME_URL)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


def test_cookie_is_secure_when_enabled_in_settings() -> None:
    app = create_app(make_test_settings(session_cookie_secure=True))
    service = AuthService(
        InMemoryUserRepository(),
        Argon2PasswordHasher(),
        JwtTokenService(TEST_JWT_SECRET, SESSION_LIFETIME),
    )
    app.dependency_overrides[get_auth_service] = lambda: service
    with TestClient(app) as client:
        client.post(REGISTER_URL, json=REGISTER_BODY)
        response = client.post(LOGIN_URL, json=LOGIN_BODY)

    assert "Secure" in response.headers["set-cookie"]


@pytest.mark.integration
@pytest.mark.ac("AC-02.1")
def test_register_login_me_logout_with_real_database(db_client: TestClient) -> None:
    db_client.post(REGISTER_URL, json=REGISTER_BODY)

    assert db_client.post(LOGIN_URL, json=LOGIN_BODY).status_code == 204
    assert db_client.get(ME_URL).json()["email"] == EMAIL
    assert db_client.post(LOGOUT_URL).status_code == 204
    assert db_client.get(ME_URL).status_code == 401
