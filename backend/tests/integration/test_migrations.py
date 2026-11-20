"""Alembic migration'ları gerçek PostgreSQL'e karşı (Testcontainers).

Her migration boş bir veritabanına sırayla uygulanabilmeli ve sonra geri alınabilmeli.
Tablolar eklendikçe (#9 `pages` …) bu test onları da kendiliğinden kapsar.
"""

from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from sqlalchemy import inspect
from testcontainers.community.postgres import PostgresContainer

from kovan.infrastructure.db.engine import create_db_engine
from kovan.infrastructure.db.tables import metadata
from tests.integration.containers import require_docker

BACKEND_DIR = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def postgres_url() -> Iterator[str]:
    require_docker()
    with PostgresContainer("postgres:16-alpine", driver="psycopg") as postgres:
        yield postgres.get_connection_url()


def alembic_config(database_url: str) -> Config:
    config = Config(BACKEND_DIR / "alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    config.attributes["configure_logger"] = False  # testlerin log ayarına dokunma
    return config


def table_names(database_url: str) -> set[str]:
    engine = create_db_engine(database_url)
    try:
        return set(inspect(engine).get_table_names())
    finally:
        engine.dispose()


@pytest.mark.integration
def test_migrations_upgrade_to_head_and_downgrade_to_base(postgres_url: str) -> None:
    config = alembic_config(postgres_url)

    command.upgrade(config, "head")
    assert set(metadata.tables) <= table_names(postgres_url)

    command.downgrade(config, "base")
    assert table_names(postgres_url) <= {"alembic_version"}


@pytest.mark.integration
def test_migrations_match_table_definitions(postgres_url: str) -> None:
    """tables.py'de değişip migration'ı yazılmamış bir tablo/sütun varsa bu test düşer."""
    command.upgrade(alembic_config(postgres_url), "head")
    engine = create_db_engine(postgres_url)
    try:
        with engine.connect() as connection:
            differences = compare_metadata(MigrationContext.configure(connection), metadata)
    finally:
        engine.dispose()

    assert differences == []
