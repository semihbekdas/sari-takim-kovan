from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from kovan.config import Settings
from kovan.main import create_app
from tests.fakes import UNREACHABLE_DATABASE_URL


@pytest.fixture
def settings() -> Settings:
    return Settings(database_url=UNREACHABLE_DATABASE_URL, log_level="WARNING")


@pytest.fixture
def app(settings: Settings) -> FastAPI:
    return create_app(settings)


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
