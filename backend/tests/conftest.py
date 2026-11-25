from collections.abc import Iterator

import pytest
from alembic import command
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from testcontainers.community.postgres import PostgresContainer

from kovan.config import Settings
from kovan.infrastructure.db.engine import create_db_engine
from kovan.main import create_app
from tests.fakes import make_test_settings
from tests.integration.containers import require_docker
from tests.integration.database import POSTGRES_IMAGE, alembic_config


@pytest.fixture
def settings() -> Settings:
    return make_test_settings()


@pytest.fixture
def app(settings: Settings) -> FastAPI:
    return create_app(settings)


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def postgres_url() -> Iterator[str]:
    """Tüm migration'ları uygulanmış gerçek PostgreSQL'in adresi (Testcontainers).

    Test oturumu boyunca tek bir konteyner açılır ve tüm entegrasyon testleri onu paylaşır.
    Docker yoksa test yerelde atlanır, CI'da hata verir (`require_docker`).
    Tablo kullanan testler (#9 `pages`, #11 `users` …) bu fixture'ı veya `db_engine`'i ister.
    """
    require_docker()
    with PostgresContainer(POSTGRES_IMAGE, driver="psycopg") as postgres:
        url = postgres.get_connection_url()
        command.upgrade(alembic_config(url), "head")
        yield url


@pytest.fixture(scope="session")
def db_engine(postgres_url: str) -> Iterator[Engine]:
    """Migration'ları uygulanmış veritabanına bağlı SQLAlchemy engine."""
    engine = create_db_engine(postgres_url)
    try:
        yield engine
    finally:
        engine.dispose()
