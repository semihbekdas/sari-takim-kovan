"""POST /api/v1/auth/register kabul testleri (US-01)."""

from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine, select

from kovan.api.deps import get_auth_service
from kovan.application.auth_service import AuthService
from kovan.infrastructure.db.tables import users
from kovan.main import create_app
from tests.fakes import FakePasswordHasher, InMemoryUserRepository, make_test_settings

REGISTER_URL = "/api/v1/auth/register"
VALID_BODY = {"email": "Ayse@Ornek.com", "password": "gizli-sifre", "display_name": "Ayşe Y."}


@pytest.fixture
def db_client(clean_users: Engine, postgres_url: str) -> Iterator[TestClient]:
    """Gerçek PostgreSQL'e bağlı uygulama (Testcontainers)."""
    app = create_app(make_test_settings(database_url=postgres_url))
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


@pytest.fixture
def fake_client(app: FastAPI, client: TestClient) -> TestClient:
    """Bellekteki kullanıcı deposuyla çalışan uygulama: Docker gerekmez."""
    service = AuthService(InMemoryUserRepository(), FakePasswordHasher())
    app.dependency_overrides[get_auth_service] = lambda: service
    return client


@pytest.mark.integration
@pytest.mark.ac("AC-01.1")
def test_register_with_valid_data_returns_201_without_password(db_client: TestClient) -> None:
    response = db_client.post(REGISTER_URL, json=VALID_BODY)

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {"id", "email", "display_name", "created_at"}
    assert body["email"] == "ayse@ornek.com"
    assert body["display_name"] == "Ayşe Y."
    assert "gizli-sifre" not in response.text


@pytest.mark.integration
@pytest.mark.ac("AC-01.2")
def test_register_with_existing_email_case_insensitive_returns_409(db_client: TestClient) -> None:
    db_client.post(REGISTER_URL, json=VALID_BODY)

    response = db_client.post(REGISTER_URL, json={**VALID_BODY, "email": "ayse@ornek.com"})

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "EMAIL_TAKEN"


@pytest.mark.integration
@pytest.mark.ac("AC-01.4")
def test_registered_user_password_is_stored_as_argon2_hash(
    db_client: TestClient, clean_users: Engine
) -> None:
    db_client.post(REGISTER_URL, json=VALID_BODY)

    with clean_users.connect() as connection:
        stored_hash = connection.execute(select(users.c.password_hash)).scalar_one()

    assert stored_hash.startswith("$argon2id$")
    assert "gizli-sifre" not in stored_hash


@pytest.mark.ac("AC-01.3")
def test_register_with_short_password_returns_422(fake_client: TestClient) -> None:
    response = fake_client.post(REGISTER_URL, json={**VALID_BODY, "password": "kisa"})

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["rule"] == "R-02"
    assert error["message"] == "Şifre en az 8 karakter olmalı."
    assert "kisa" not in response.text


@pytest.mark.ac("AC-01.3")
def test_register_with_invalid_email_returns_422(fake_client: TestClient) -> None:
    response = fake_client.post(REGISTER_URL, json={**VALID_BODY, "email": "ayse"})

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["rule"] == "R-01"
    assert error["code"] == "EMAIL_INVALID"


def test_register_with_too_short_display_name_returns_validation_error(
    fake_client: TestClient,
) -> None:
    response = fake_client.post(REGISTER_URL, json={**VALID_BODY, "display_name": "A"})

    assert response.status_code == 422
    assert response.json()["error"]["details"] == [
        {"field": "body.display_name", "message": "Çok kısa."}
    ]
