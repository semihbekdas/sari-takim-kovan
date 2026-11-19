"""Uygulama ayarları. Değerler ortam değişkenlerinden ve repo kökündeki `.env` dosyasından okunur.

Tüm değişkenler ve açıklamaları: `.env.example`, docs/architecture.md § 8.
"""

from pathlib import Path
from typing import Literal

from pydantic import PositiveFloat, PositiveInt, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# src/kovan/config.py -> repo kökü
_REPO_ROOT_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_REPO_ROOT_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # Yapay zeka (ADR-006). Varsayılan "fake": API anahtarı gerekmez.
    chat_provider: Literal["fake", "anthropic", "openai_compatible"] = "fake"
    chat_model: str = "claude-opus-5-5"
    chat_base_url: str | None = None
    chat_max_tokens: PositiveInt = 4096
    chat_effort: Literal["low", "medium", "high", "xhigh", "max"] | None = "low"
    embedding_provider: Literal["fake", "openai_compatible"] = "fake"
    embedding_base_url: str = "https://api.openai.com/v1"
    embedding_model: str = "text-embedding-3-small"
    embedding_dim: PositiveInt = 1536
    # Anahtarlar sağlayıcıya göre değil göreve göre adlandırılır: Her anahtar yalnızca kendi
    # sağlayıcısına gönderilir (başka bir sağlayıcının anahtarına düşülmez).
    chat_api_key: SecretStr | None = None
    embedding_api_key: SecretStr | None = None
    ai_timeout_seconds: PositiveFloat = 30.0

    @field_validator(
        "chat_base_url",
        "chat_effort",
        "chat_api_key",
        "embedding_api_key",
        mode="before",
    )
    @classmethod
    def _empty_means_unset(cls, value: object) -> object:
        # .env'de "CHAT_EFFORT=" gibi boş bırakılan değerler "ayarlanmamış" sayılır.
        return None if value == "" else value


def load_settings() -> Settings:
    """Ayarları ortamdan yükler. Zorunlu bir değer eksikse açıklayıcı bir hata verir."""
    return Settings()
