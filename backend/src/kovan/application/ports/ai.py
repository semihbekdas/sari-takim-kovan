"""Yapay zeka port'ları (ADR-006).

Gerçek uygulamalar `infrastructure/ai` altındadır; testler ve "fake" mod sahtelerini kullanır.
Uygulamalar dış servis hatalarını `ExternalServiceError`'a çevirir.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal, Protocol

FinishReason = Literal["stop", "length", "refusal"]


@dataclass(frozen=True)
class ChatMessage:
    role: Literal["user", "assistant"]
    content: str


@dataclass(frozen=True)
class ChatCompletion:
    text: str
    model: str
    input_tokens: int
    output_tokens: int
    finish_reason: FinishReason = "stop"


class EmbeddingProvider(Protocol):
    """Metinleri vektörlere çevirir."""

    @property
    def dimension(self) -> int: ...

    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


class ChatModel(Protocol):
    """Sistem talimatı ve mesajlardan bir cevap üretir."""

    def complete(
        self, *, system: str, messages: Sequence[ChatMessage], max_tokens: int
    ) -> ChatCompletion: ...
