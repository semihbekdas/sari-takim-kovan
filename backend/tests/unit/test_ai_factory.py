"""Yapay zeka fabrikası: ayarlara göre doğru adaptör, doğru anahtar ve sınırlı yeniden deneme."""

import pytest
from pydantic import SecretStr, ValidationError

from kovan.config import Settings
from kovan.infrastructure.ai.anthropic_chat import AnthropicChatModel
from kovan.infrastructure.ai.factory import (
    ANTHROPIC_API_URL,
    OPENAI_API_URL,
    SDK_MAX_RETRIES,
    build_chat_model,
    build_embedding_provider,
)
from kovan.infrastructure.ai.fake import FakeChatModel, FakeEmbeddingProvider
from kovan.infrastructure.ai.openai_compatible import (
    OpenAICompatibleChatModel,
    OpenAICompatibleEmbeddingProvider,
)
from tests.fakes import UNREACHABLE_DATABASE_URL, make_test_settings


def _settings(**overrides: object) -> Settings:
    return make_test_settings(**{"embedding_dim": 32, **overrides})


def test_default_mode_is_fake_and_needs_no_keys() -> None:
    settings = _settings()

    assert isinstance(build_chat_model(settings), FakeChatModel)
    embedding = build_embedding_provider(settings)
    assert isinstance(embedding, FakeEmbeddingProvider)
    assert embedding.dimension == 32


def test_anthropic_requires_an_api_key() -> None:
    with pytest.raises(ValueError, match="CHAT_API_KEY"):
        build_chat_model(_settings(chat_provider="anthropic"))


def test_anthropic_chat_model_is_built_with_key() -> None:
    settings = _settings(chat_provider="anthropic", chat_api_key=SecretStr("k"))

    model = build_chat_model(settings)

    assert isinstance(model, AnthropicChatModel)
    assert model._client.max_retries == SDK_MAX_RETRIES


def test_ambient_base_url_variables_are_ignored(monkeypatch: pytest.MonkeyPatch) -> None:
    # Ortamdaki adres değişkenleri anahtarı ve soruları başka bir sunucuya yönlendirmemeli.
    monkeypatch.setenv("OPENAI_BASE_URL", "https://baska-sunucu.example/v1")
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://baska-sunucu.example")

    openai_model = build_chat_model(
        _settings(chat_provider="openai_compatible", chat_api_key=SecretStr("k"))
    )
    anthropic_model = build_chat_model(
        _settings(chat_provider="anthropic", chat_api_key=SecretStr("k"))
    )

    assert isinstance(openai_model, OpenAICompatibleChatModel)
    assert isinstance(anthropic_model, AnthropicChatModel)
    assert str(openai_model._client.base_url) == OPENAI_API_URL + "/"
    assert str(anthropic_model._client.base_url) == ANTHROPIC_API_URL


@pytest.mark.parametrize("field", ["embedding_dim", "chat_max_tokens", "ai_timeout_seconds"])
def test_non_positive_numeric_settings_are_rejected(field: str) -> None:
    with pytest.raises(ValidationError, match=field):
        _settings(**{field: 0})


def test_openai_compatible_chat_model_is_built_with_key() -> None:
    settings = _settings(chat_provider="openai_compatible", chat_api_key=SecretStr("k"))

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


def test_embedding_never_falls_back_to_the_chat_key() -> None:
    # Sohbet anahtarı başka bir sağlayıcıya (EMBEDDING_BASE_URL) gönderilmemeli.
    settings = _settings(embedding_provider="openai_compatible", chat_api_key=SecretStr("k"))

    with pytest.raises(ValueError, match="EMBEDDING_API_KEY"):
        build_embedding_provider(settings)


def test_empty_env_values_mean_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("CHAT_EFFORT", "CHAT_BASE_URL", "CHAT_API_KEY"):
        monkeypatch.setenv(name, "")

    settings = Settings(_env_file=None, database_url=UNREACHABLE_DATABASE_URL)

    assert settings.chat_effort is None
    assert settings.chat_base_url is None
    assert settings.chat_api_key is None
