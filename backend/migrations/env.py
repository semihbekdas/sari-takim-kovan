"""Alembic çalışma ortamı: Veritabanı adresini uygulama ayarlarından alır (ADR-003).

Adres önce Alembic yapılandırmasındaki `sqlalchemy.url`'den okunur (testler bunu kullanır);
yoksa uygulamanın kendi ayarlarından (`DATABASE_URL`, `.env`) gelir. Böylece adres tek yerde
tanımlıdır ve şifre alembic.ini'ye yazılmaz.
"""

from logging.config import fileConfig

from alembic import context

from kovan.config import load_settings
from kovan.infrastructure.db.engine import create_db_engine
from kovan.infrastructure.db.tables import metadata

config = context.config

if config.config_file_name is not None and config.attributes.get("configure_logger", True):
    fileConfig(config.config_file_name)

target_metadata = metadata


def database_url() -> str:
    return config.get_main_option("sqlalchemy.url") or load_settings().database_url


def run_migrations_offline() -> None:
    """Veritabanına bağlanmadan SQL çıktısı üretir: `alembic upgrade head --sql`."""
    context.configure(
        url=database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_db_engine(database_url())
    try:
        with engine.connect() as connection:
            context.configure(connection=connection, target_metadata=target_metadata)
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
