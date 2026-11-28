"""Sayfa oluşturma, görüntüleme, kaydetme ve ağaç kabul testleri (US-03, US-04, US-05; #9).

Gerçek PostgreSQL ve gerçek oturum. `clean_users` kullanıcıları (ve CASCADE ile sayfaları) siler.
"""

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from kovan.main import create_app
from tests.fakes import make_test_settings

pytestmark = pytest.mark.integration

PAGES_URL = "/api/v1/pages"
PASSWORD = "gizli-sifre"
PARAGRAPH = [{"type": "paragraph", "content": [{"type": "text", "text": "Merhaba"}]}]
MISSING_ID = "00000000-0000-0000-0000-000000000000"


def logged_in_client(app: FastAPI, email: str) -> TestClient:
    client = TestClient(app, raise_server_exceptions=False)
    body = {"email": email, "password": PASSWORD}
    client.post("/api/v1/auth/register", json={**body, "display_name": "Test"})
    assert client.post("/api/v1/auth/login", json=body).status_code == 204
    return client


@pytest.fixture
def app(clean_users: Engine, postgres_url: str) -> FastAPI:
    return create_app(make_test_settings(database_url=postgres_url))


@pytest.fixture
def ayse(app: FastAPI) -> Iterator[TestClient]:
    with logged_in_client(app, "ayse@ornek.com") as client:
        yield client


@pytest.fixture
def mehmet(app: FastAPI) -> Iterator[TestClient]:
    with logged_in_client(app, "mehmet@ornek.com") as client:
        yield client


def create(client: TestClient, **body: Any) -> dict[str, Any]:
    response = client.post(PAGES_URL, json=body)
    assert response.status_code == 201
    return dict(response.json())


@pytest.mark.ac("AC-03.1")
def test_create_page_without_title_gets_default_title(ayse: TestClient) -> None:
    page = create(ayse)

    assert page["title"] == "Adsız"
    assert page["content"] == []
    assert page["version"] == 1
    assert page["index_status"] == "PENDING"
    assert page["parent_id"] is None
    assert page["breadcrumbs"] == []


@pytest.mark.ac("AC-03.2")
def test_create_page_with_title_longer_than_200_returns_422(ayse: TestClient) -> None:
    response = ayse.post(PAGES_URL, json={"title": "a" * 201})

    assert response.status_code == 422
    assert response.json()["error"]["rule"] == "R-03"


@pytest.mark.ac("AC-03.3")
@pytest.mark.ac("AC-05.2")
def test_get_own_page_returns_content_version_status_breadcrumbs(ayse: TestClient) -> None:
    root = create(ayse, title="Dersler")
    child = create(ayse, title="Veritabanı", parent_id=root["id"])
    page = create(ayse, title="Normalizasyon", parent_id=child["id"], content=PARAGRAPH)

    response = ayse.get(f"{PAGES_URL}/{page['id']}")

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Normalizasyon"
    assert body["content"] == PARAGRAPH
    assert (body["version"], body["index_status"]) == (1, "PENDING")
    assert [crumb["title"] for crumb in body["breadcrumbs"]] == ["Dersler", "Veritabanı"]


@pytest.mark.ac("AC-03.4")
def test_get_other_users_page_returns_404(ayse: TestClient, mehmet: TestClient) -> None:
    page = create(ayse, title="Gizli not")

    other = mehmet.get(f"{PAGES_URL}/{page['id']}")
    missing = mehmet.get(f"{PAGES_URL}/{MISSING_ID}")

    assert other.status_code == missing.status_code == 404
    # Başkasının sayfası ile hiç olmayan sayfa aynı yanıtı alır: varlığı belli olmaz.
    assert other.json()["error"]["code"] == missing.json()["error"]["code"] == "PAGE_NOT_FOUND"
    assert "Gizli not" not in other.text


@pytest.mark.ac("AC-05.3")
def test_create_page_under_other_users_parent_returns_404(
    ayse: TestClient, mehmet: TestClient
) -> None:
    parent = create(ayse, title="Dersler")

    response = mehmet.post(PAGES_URL, json={"title": "Alt", "parent_id": parent["id"]})

    assert response.status_code == 404


@pytest.mark.ac("AC-04.5")
def test_update_increments_version_and_keeps_new_content(ayse: TestClient) -> None:
    page = create(ayse, title="Taslak")
    url = f"{PAGES_URL}/{page['id']}"

    response = ayse.put(url, json={"title": "Son hali", "content": PARAGRAPH, "version": 1})

    assert response.status_code == 200
    assert response.json()["version"] == 2
    assert response.json()["index_status"] == "PENDING"
    saved = ayse.get(url).json()
    assert (saved["title"], saved["content"], saved["version"]) == ("Son hali", PARAGRAPH, 2)


@pytest.mark.ac("AC-04.3")
def test_update_with_stale_version_returns_409_and_keeps_content(ayse: TestClient) -> None:
    page = create(ayse, title="Taslak")
    url = f"{PAGES_URL}/{page['id']}"
    ayse.put(url, json={"title": "Sekme 1", "content": PARAGRAPH, "version": 1})

    response = ayse.put(url, json={"title": "Sekme 2", "content": [], "version": 1})

    assert response.status_code == 409
    error = response.json()["error"]
    assert (error["code"], error["rule"]) == ("VERSION_CONFLICT", "R-07")
    assert ayse.get(url).json()["title"] == "Sekme 1"


@pytest.mark.ac("AC-04.4")
def test_update_with_disallowed_block_type_returns_422(ayse: TestClient) -> None:
    page = create(ayse)

    response = ayse.put(
        f"{PAGES_URL}/{page['id']}",
        json={"title": "Tablo", "content": [{"type": "table"}], "version": 1},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "CONTENT_INVALID"


def test_other_user_cannot_update_the_page(ayse: TestClient, mehmet: TestClient) -> None:
    page = create(ayse, title="Ayşe'nin")

    response = mehmet.put(
        f"{PAGES_URL}/{page['id']}", json={"title": "Ele geçirildi", "content": [], "version": 1}
    )

    assert response.status_code == 404
    assert ayse.get(f"{PAGES_URL}/{page['id']}").json()["title"] == "Ayşe'nin"


@pytest.mark.ac("AC-05.1")
def test_tree_shows_child_under_parent_and_hides_other_users_pages(
    ayse: TestClient, mehmet: TestClient
) -> None:
    parent = create(ayse, title="Dersler")
    child = create(ayse, title="Veritabanı", parent_id=parent["id"])
    create(mehmet, title="Mehmet'in notu")

    response = ayse.get(f"{PAGES_URL}/tree")

    assert response.status_code == 200
    assert response.json() == [
        {"id": parent["id"], "parent_id": None, "title": "Dersler", "has_children": True},
        {
            "id": child["id"],
            "parent_id": parent["id"],
            "title": "Veritabanı",
            "has_children": False,
        },
    ]


@pytest.mark.ac("AC-02.4")
def test_pages_without_session_return_401(app: FastAPI) -> None:
    with TestClient(app, raise_server_exceptions=False) as anonymous:
        assert anonymous.post(PAGES_URL, json={}).status_code == 401
        assert anonymous.get(f"{PAGES_URL}/{MISSING_ID}").status_code == 401
        assert anonymous.get(f"{PAGES_URL}/tree").status_code == 401
