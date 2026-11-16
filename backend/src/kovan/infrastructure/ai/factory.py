"""Ayarlara göre doğru yapay zeka adaptörünü kurar (composition root'tan çağrılır).

Varsayılan "fake" moddur: API anahtarı olmadan da uygulama ve testler çalışır.
"""

import anthropic
import openai
from pydantic import SecretStr

from kovan.application.ports.ai import ChatModel, EmbeddingProvider
from kovan.config import Settings
from kovan.infrastructure.ai.anthropic_chat import AnthropicChatModel
from kovan.infrastructure.ai.fake import FakeChatModel, FakeEmbeddingProvider
from kovan.infrastructure.ai.openai_compatible import (
    OpenAICompatibleChatModel,
    OpenAICompatibleEmbeddingProvider,
)


def build_chat_model(settings: Settings) -> ChatModel:
    if settings.chat_provider == "anthropic":
        client = anthropic.Anthropic(
            api_key=_require(settings.anthropic_api_key, "ANTHROPIC_API_KEY"),
            timeout=settings.ai_timeout_seconds,
        )
        return AnthropicChatModel(client, model=settings.chat_model, effort=settings.chat_effort)
    if settings.chat_provider == "openai_compatible":
        openai_client = openai.OpenAI(
            api_key=_require(settings.openai_api_key, "OPENAI_API_KEY"),
            base_url=settings.chat_base_url or None,
            timeout=settings.ai_timeout_seconds,
        )
        return OpenAICompatibleChatModel(openai_client, model=settings.chat_model)
    return FakeChatModel()


def build_embedding_provider(settings: Settings) -> EmbeddingProvider:
    if settings.embedding_provider == "openai_compatible":
        key = settings.embedding_api_key or settings.openai_api_key
        client = openai.OpenAI(
            api_key=_require(key, "EMBEDDING_API_KEY veya OPENAI_API_KEY"),
            base_url=settings.embedding_base_url,
            timeout=settings.ai_timeout_seconds,
        )
        return OpenAICompatibleEmbeddingProvider(
            client, model=settings.embedding_model, dimension=settings.embedding_dim
        )
    return FakeEmbeddingProvider(dimension=settings.embedding_dim)


def _require(secret: SecretStr | None, name: str) -> str:
    value = secret.get_secret_value() if secret else ""
    if not value:
        raise ValueError(f"{name} boş. Gerçek yapay zeka sağlayıcısı için .env'e anahtar girin.")
    return value
