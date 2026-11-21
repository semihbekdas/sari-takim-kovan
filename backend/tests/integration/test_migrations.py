"""Alembic migration'ları gerçek PostgreSQL'e karşı (ortak `postgres_url` fixture'ı, conftest.py).

Her migration geri alınabilmeli ve yeniden uygulanabilmeli; tables.py ile migration'lar uyuşmalı.
Tablolar eklendikçe (#9 `pages`, #11 `users` …) bu testler onları da kendiliğinden kapsar.
"""

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext
from sqlalchemy import Engine, inspect

from kovan.infrastructure.db.tables import metadata
from tests.integration.database import alembic_config


def table_names(engine: Engine) -> set[str]:
    return set(inspect(engine).get_table_names())


@pytest.mark.integration
def test_migrations_downgrade_to_base_and_upgrade_to_head(
    postgres_url: str, db_engine: Engine
) -> None:
    config = alembic_config(postgres_url)
    assert set(metadata.tables) <= table_names(db_engine)

    try:
        command.downgrade(config, "base")
        assert table_names(db_engine) <= {"alembic_version"}
    finally:
        # Veritabanı diğer testlerle paylaşıldığı için her durumda eski hâline döndürülür.
        command.upgrade(config, "head")

    assert set(metadata.tables) <= table_names(db_engine)


@pytest.mark.integration
def test_migrations_match_table_definitions(db_engine: Engine) -> None:
    """tables.py'de değişip migration'ı yazılmamış bir tablo/sütun varsa bu test düşer."""
    with db_engine.connect() as connection:
        differences = compare_metadata(MigrationContext.configure(connection), metadata)

    assert differences == []
