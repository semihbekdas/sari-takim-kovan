"""SQLAlchemy engine oluşturma."""

from sqlalchemy import Engine, create_engine

CONNECT_TIMEOUT_SECONDS = 5


def create_db_engine(database_url: str) -> Engine:
    """Bağlantı havuzlu bir engine oluşturur. Bağlantı ilk kullanımda açılır.

    `hide_parameters`: SQL hata mesajlarına sorgu parametreleri (e-posta, şifre özeti vb.)
    yazılmaz; bu mesajlar loglara düşer.
    """
    return create_engine(
        database_url,
        pool_pre_ping=True,
        hide_parameters=True,
        connect_args={"connect_timeout": CONNECT_TIMEOUT_SECONDS},
    )
