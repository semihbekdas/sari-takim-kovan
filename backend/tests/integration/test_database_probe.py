"""`DatabaseProbe` gerçek PostgreSQL'e karşı (Testcontainers) ve erişilemeyen adrese karşı."""

import pytest
from sqlalchemy import Engine

from kovan.infrastructure.db.engine import create_db_engine
from kovan.infrastructure.db.probe import DatabaseProbe
from tests.fakes import UNREACHABLE_DATABASE_URL


def test_probe_reports_down_when_database_is_unreachable() -> None:
    probe = DatabaseProbe(create_db_engine(UNREACHABLE_DATABASE_URL))

    assert probe.is_ready() is False


@pytest.mark.integration
def test_probe_reports_up_when_database_is_reachable(db_engine: Engine) -> None:
    assert DatabaseProbe(db_engine).is_ready() is True
