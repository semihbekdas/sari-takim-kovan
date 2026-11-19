"""Ayarlara göre doğru yapay zeka adaptörünü kurar.

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

# SDK'lar varsayılan olarak 2 kez yeniden dener; zaman aşımında kullanıcı ~3 × AI_TIMEOUT_SECONDS
# beklerdi. Bir yeniden deneme geçici hataya yeter; indeksleme zaten kendi yeniden denemesini yapar.
SDK_MAX_RETRIES = 1

# Adres her zaman açıkça verilir: Aksi halde SDK'lar ortamdaki OPENAI_BASE_URL / ANTHROPIC_BASE_URL
# değişkenini kullanır ve anahtar ile sorular Kovan'ın ayarlamadığı bir adrese gidebilir.
ANTHROPIC_API_URL = "https://api.anthropic.com"
OPENAI_API_URL = "https://api.openai.com/v1"


def build_chat_model(settings: Settings) -> ChatModel:
    if settings.chat_provider == "anthropic":
        client = anthropic.Anthropic(
            api_key=_require(settings.chat_api_key, "CHAT_API_KEY"),
            base_url=ANTHROPIC_API_URL,
            timeout=settings.ai_timeout_seconds,
            max_retries=SDK_MAX_RETRIES,
        )
        return AnthropicChatModel(client, model=settings.chat_model, effort=settings.chat_effort)
    if settings.chat_provider == "openai_compatible":
        openai_client = openai.OpenAI(
            api_key=_require(settings.chat_api_key, "CHAT_API_KEY"),
            base_url=settings.chat_base_url or OPENAI_API_URL,
            timeout=settings.ai_timeout_seconds,
            max_retries=SDK_MAX_RETRIES,
        )
        return OpenAICompatibleChatModel(openai_client, model=settings.chat_model)
    return FakeChatModel()


def build_embedding_provider(settings: Settings) -> EmbeddingProvider:
    if settings.embedding_provider == "openai_compatible":
        client = openai.OpenAI(
            api_key=_require(settings.embedding_api_key, "EMBEDDING_API_KEY"),
            base_url=settings.embedding_base_url,
            timeout=settings.ai_timeout_seconds,
            max_retries=SDK_MAX_RETRIES,
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
