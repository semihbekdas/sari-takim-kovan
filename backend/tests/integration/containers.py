"""Testcontainers testleri için Docker kontrolü.

Yerelde Docker kapalıysa entegrasyon testleri atlanır; geliştirici birim testleri yine çalıştırır.
CI'da ise (GitHub Actions `CI=true` ortam değişkenini kurar) Docker zorunludur: Docker'a
ulaşılamazsa test atlanmaz, hata verir. Böylece CI, entegrasyon testlerini hiç çalıştırmadan
yeşil yanamaz (KURALLAR.md § 5).
"""

import os

import docker
import pytest
from docker.errors import DockerException


def require_docker() -> None:
    try:
        docker.from_env().ping()
    except DockerException as error:
        reason = f"Docker'a ulaşılamadı: {error}"
        if os.environ.get("CI"):
            pytest.fail(f"{reason} CI'da entegrasyon testleri zorunludur.")
        pytest.skip(f"{reason} Yerel çalıştırmada entegrasyon testi atlandı.")
