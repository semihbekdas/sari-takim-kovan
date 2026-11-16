from typing import Any

import pytest
from pydantic import SecretStr

from kovan.config import Settings
from kovan.infrastructure.ai.anthropic_chat import AnthropicChatModel
from kovan.infrastructure.ai.factory import build_chat_model, build_embedding_provider
from kovan.infrastructure.ai.fake import FakeChatModel, FakeEmbeddingProvider
from kovan.infrastructure.ai.openai_compatible import (
    OpenAICompatibleChatModel,
    OpenAICompatibleEmbeddingProvider,
)
from tests.fakes import UNREACHABLE_DATABASE_URL


def _settings(**overrides: Any) -> Settings:
    # Testler .env dosyasından etkilenmesin diye tüm yapay zeka ayarları açıkça verilir.
    values: dict[str, Any] = {
        "database_url": UNREACHABLE_DATABASE_URL,
        "chat_provider": "fake",
        "embedding_provider": "fake",
        "anthropic_api_key": None,
        "openai_api_key": None,
        "embedding_api_key": None,
        "embedding_dim": 32,
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def test_default_mode_is_fake_and_needs_no_keys() -> None:
    settings = _settings()

    assert isinstance(build_chat_model(settings), FakeChatModel)
    embedding = build_embedding_provider(settings)
    assert isinstance(embedding, FakeEmbeddingProvider)
    assert embedding.dimension == 32


def test_anthropic_requires_an_api_key() -> None:
    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
        build_chat_model(_settings(chat_provider="anthropic"))


def test_anthropic_chat_model_is_built_with_key() -> None:
    settings = _settings(chat_provider="anthropic", anthropic_api_key=SecretStr("k"))

    assert isinstance(build_chat_model(settings), AnthropicChatModel)


def test_openai_compatible_chat_model_is_built_with_key() -> None:
    settings = _settings(chat_provider="openai_compatible", openai_api_key=SecretStr("k"))

    assert isinstance(build_chat_model(settings), OpenAICompatibleChatModel)


def test_embedding_provider_uses_embedding_key_and_dimension() -> None:
    settings = _settings(
        embedding_provider="openai_compatible", embedding_api_key=SecretStr("k"), embedding_dim=1024
    )

    provider = build_embedding_provider(settings)

    assert isinstance(provider, OpenAICompatibleEmbeddingProvider)
    assert provider.dimension == 1024


def test_real_embedding_provider_without_any_key_fails_fast() -> None:
    with pytest.raises(ValueError, match="EMBEDDING_API_KEY"):
        build_embedding_provider(_settings(embedding_provider="openai_compatible"))


def test_empty_env_values_mean_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("CHAT_EFFORT", "CHAT_BASE_URL", "ANTHROPIC_API_KEY"):
        monkeypatch.setenv(name, "")

    settings = Settings(_env_file=None, database_url=UNREACHABLE_DATABASE_URL)

    assert settings.chat_effort is None
    assert settings.chat_base_url is None
    assert settings.anthropic_api_key is None
