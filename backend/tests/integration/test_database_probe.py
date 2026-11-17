"""`DatabaseProbe` gerçek PostgreSQL'e karşı (Testcontainers) ve erişilemeyen adrese karşı."""

from collections.abc import Iterator

import pytest
from testcontainers.community.postgres import PostgresContainer

from kovan.infrastructure.db.engine import create_db_engine
from kovan.infrastructure.db.probe import DatabaseProbe
from tests.fakes import UNREACHABLE_DATABASE_URL
from tests.integration.containers import require_docker


@pytest.fixture(scope="module")
def postgres_url() -> Iterator[str]:
    require_docker()
    with PostgresContainer("postgres:16-alpine", driver="psycopg") as postgres:
        yield postgres.get_connection_url()


def test_probe_reports_down_when_database_is_unreachable() -> None:
    probe = DatabaseProbe(create_db_engine(UNREACHABLE_DATABASE_URL))

    assert probe.is_ready() is False


@pytest.mark.integration
def test_probe_reports_up_when_database_is_reachable(postgres_url: str) -> None:
    engine = create_db_engine(postgres_url)
    try:
        assert DatabaseProbe(engine).is_ready() is True
    finally:
        engine.dispose()
