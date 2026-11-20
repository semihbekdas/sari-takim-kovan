"""OpenAI uyumlu API adaptörleri (ADR-006).

Resmi `openai` SDK'sı `base_url` ile OpenAI, Google Gemini (OpenAI uyumlu uç nokta) veya
OpenRouter'a (ör. BAAI bge-m3) bağlanır. Yerel modeller kullanılmaz (ADR-006).
"""

from collections.abc import Sequence

import openai
from openai.types.chat import ChatCompletionMessageParam

from kovan.application.ports.ai import ChatCompletion, ChatMessage, FinishReason
from kovan.infrastructure.ai.errors import to_external_error

DEFAULT_BATCH_SIZE = 64

_FINISH_REASONS: dict[str, FinishReason] = {"length": "length", "content_filter": "refusal"}

_ERROR_REASONS: tuple[tuple[type[Exception], str], ...] = (
    (openai.APITimeoutError, "timeout"),
    (openai.APIConnectionError, "connection"),
    (openai.RateLimitError, "rate_limited"),
    (openai.AuthenticationError, "authentication"),
    (openai.APIStatusError, "http_error"),
)


class OpenAICompatibleEmbeddingProvider:
    def __init__(
        self,
        client: openai.OpenAI,
        *,
        model: str,
        dimension: int,
        batch_size: int = DEFAULT_BATCH_SIZE,
    ) -> None:
        self._client = client
        self._model = model
        self._dimension = dimension
        self._batch_size = batch_size

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for start in range(0, len(texts), self._batch_size):
            vectors.extend(self._embed_batch(texts[start : start + self._batch_size]))
        return vectors

    def _embed_batch(self, batch: Sequence[str]) -> list[list[float]]:
        try:
            response = self._client.embeddings.create(model=self._model, input=list(batch))
        except openai.APIError as error:
            raise to_external_error(error, provider="openai", reasons=_ERROR_REASONS) from error
        vectors = [item.embedding for item in sorted(response.data, key=lambda item: item.index)]
        self._check_dimension(vectors)
        return vectors

    def _check_dimension(self, vectors: list[list[float]]) -> None:
        wrong = next((len(vector) for vector in vectors if len(vector) != self._dimension), None)
        if wrong is not None:
            # Yapılandırma hatası: Yanlış boyutlu vektörler Qdrant'a yazılmasın diye hata verilir.
            # Ayar düzeltilene kadar hiçbir sayfa indekslenemez.
            raise ValueError(
                f"EMBEDDING_DIM={self._dimension} ama '{self._model}' {wrong} boyutlu "
                "vektör döndü. .env'deki EMBEDDING_DIM'i düzeltip "
                "`uv run python -m kovan.cli reindex --all` çalıştırın."
            )


class OpenAICompatibleChatModel:
    def __init__(self, client: openai.OpenAI, *, model: str) -> None:
        self._client = client
        self._model = model

    def complete(
        self, *, system: str, messages: Sequence[ChatMessage], max_tokens: int
    ) -> ChatCompletion:
        api_messages: list[ChatCompletionMessageParam] = [{"role": "system", "content": system}]
        api_messages.extend(_to_openai_message(message) for message in messages)
        try:
            response = self._client.chat.completions.create(
                model=self._model, messages=api_messages, max_completion_tokens=max_tokens
            )
        except openai.APIError as error:
            raise to_external_error(error, provider="openai", reasons=_ERROR_REASONS) from error

        usage = response.usage
        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0
        # Gemini güvenlik nedeniyle engellediğinde cevap seçeneği veya mesaj hiç gelmeyebilir.
        choice = response.choices[0] if response.choices else None
        message = getattr(choice, "message", None)
        if choice is None or message is None:
            return ChatCompletion("", response.model, input_tokens, 0, finish_reason="refusal")
        return ChatCompletion(
            text=message.content or "",
            model=response.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            finish_reason=_FINISH_REASONS.get(choice.finish_reason, "stop"),
        )


def _to_openai_message(message: ChatMessage) -> ChatCompletionMessageParam:
    if message.role == "user":
        return {"role": "user", "content": message.content}
    return {"role": "assistant", "content": message.content}
