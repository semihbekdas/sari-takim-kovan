"""Testlerde kullanılan fake port uygulamaları, sabitler ve test ayarları."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from kovan.config import Settings
from kovan.domain.errors import ConflictError
from kovan.domain.users import User

# Bağlanılamayan bir adres: Testler gerçek veritabanına ihtiyaç duymaz.
UNREACHABLE_DATABASE_URL = "postgresql+psycopg://kovan:kovan@127.0.0.1:1/kovan"


def make_test_settings(**overrides: Any) -> Settings:
    """Testler için ayarlar: Geliştiricinin `.env` dosyası okunmaz (`_env_file=None`).

    Böylece gerçek API anahtarı olan bir makinede bile testler aynı, güvenli ayarlarla çalışır.
    Ortam değişkenleri de okunduğu için yapay zeka ayarları açıkça "fake" ve anahtarsız verilir.
    """
    values: dict[str, Any] = {
        "database_url": UNREACHABLE_DATABASE_URL,
        "log_level": "WARNING",
        "chat_provider": "fake",
        "embedding_provider": "fake",
        "chat_api_key": None,
        "embedding_api_key": None,
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


@dataclass
class FakeProbe:
    """`ReadinessProbe` port'unun test karşılığı."""

    name: str
    ready: bool

    def is_ready(self) -> bool:
        return self.ready


class FakePasswordHasher:
    """`PasswordHasher` port'unun test karşılığı: Hash'i okunabilir tutar."""

    def hash(self, password: str) -> str:
        return f"hashed:{password}"


@dataclass
class InMemoryUserRepository:
    """`UserRepository` port'unun bellekte çalışan test karşılığı."""

    users: list[User] = field(default_factory=list)

    def add(self, *, user_id: UUID, email: str, display_name: str, password_hash: str) -> User:
        if any(user.email == email for user in self.users):
            raise ConflictError("Bu e-posta zaten kayıtlı.", code="EMAIL_TAKEN")
        user = User(user_id, email, display_name, password_hash, datetime.now(UTC))
        self.users.append(user)
        return user
