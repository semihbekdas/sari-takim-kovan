"""Veritabanı engine ayarları."""

from kovan.infrastructure.db.engine import create_db_engine
from tests.fakes import UNREACHABLE_DATABASE_URL


def test_sql_error_messages_do_not_include_query_parameters() -> None:
    engine = create_db_engine(UNREACHABLE_DATABASE_URL)
    try:
        assert engine.hide_parameters is True
    finally:
        engine.dispose()
