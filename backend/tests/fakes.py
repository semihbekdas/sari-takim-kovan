"""Testlerde kullanılan fake port uygulamaları, sabitler ve test ayarları."""

from dataclasses import dataclass
from typing import Any

from kovan.config import Settings

# Bağlanılamayan bir adres: Testler gerçek veritabanına ihtiyaç duymaz.
UNREACHABLE_DATABASE_URL = "postgresql+psycopg://kovan:kovan@127.0.0.1:1/kovan"


def make_test_settings(**overrides: Any) -> Settings:
    """Testler için ayarlar: Geliştiricinin `.env` dosyası okunmaz (`_env_file=None`).

    Böylece gerçek API anahtarı olan bir makinede bile testler aynı, güvenli ayarlarla çalışır.
    """
    values: dict[str, Any] = {"database_url": UNREACHABLE_DATABASE_URL, "log_level": "WARNING"}
    values.update(overrides)
    return Settings(_env_file=None, **values)


@dataclass
class FakeProbe:
    """`ReadinessProbe` port'unun test karşılığı."""

    name: str
    ready: bool

    def is_ready(self) -> bool:
        return self.ready
