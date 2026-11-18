"""Uygulama ayarları. Değerler ortam değişkenlerinden ve repo kökündeki `.env` dosyasından okunur.

Tüm değişkenler ve açıklamaları: `.env.example`, docs/architecture.md § 8.
"""

from pathlib import Path
from typing import Literal

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


def load_settings() -> Settings:
    """Ayarları ortamdan yükler. Zorunlu bir değer eksikse açıklayıcı bir hata verir."""
    return Settings()
