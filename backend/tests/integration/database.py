"""Entegrasyon testleri için ortak PostgreSQL yardımcıları (Testcontainers + Alembic)."""

from pathlib import Path

from alembic.config import Config

POSTGRES_IMAGE = "postgres:16-alpine"  # docker-compose.yml ile aynı sürüm

BACKEND_DIR = Path(__file__).resolve().parents[2]


def alembic_config(database_url: str) -> Config:
    """backend/alembic.ini'yi verilen veritabanı adresine yönlendirir."""
    config = Config(BACKEND_DIR / "alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    config.attributes["configure_logger"] = False  # testlerin log ayarına dokunma
    return config
