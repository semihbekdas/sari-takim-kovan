"""Claude (Anthropic) sohbet modeli adaptörü (ADR-006). Resmi `anthropic` SDK'sını kullanır."""

from collections.abc import Sequence
from typing import Literal

import anthropic
from anthropic.types.beta import (
    BetaAssistantMessageParam,
    BetaMessageParam,
    BetaTextBlock,
    BetaUserMessageParam,
)

from kovan.application.ports.ai import ChatCompletion, ChatMessage, FinishReason
from kovan.infrastructure.ai.errors import to_external_error

Effort = Literal["low", "medium", "high", "xhigh", "max"]

# Model bir isteği güvenlik nedeniyle reddederse sunucu tarafında yedek modele geçilir.
# "default", yedek desteklemeyen modellerde yok sayılır (hata vermez).
_FALLBACK_BETA = "server-side-fallback-2026-07-01"

_FINISH_REASONS: dict[str, FinishReason] = {
    "max_tokens": "length",
    "model_context_window_exceeded": "length",  # bağlam penceresi doldu, cevap kesildi
    "refusal": "refusal",
}

_ERROR_REASONS: tuple[tuple[type[Exception], str], ...] = (
    (anthropic.APITimeoutError, "timeout"),
    (anthropic.APIConnectionError, "connection"),
    (anthropic.RateLimitError, "rate_limited"),
    (anthropic.AuthenticationError, "authentication"),
    (anthropic.APIStatusError, "http_error"),
)


class AnthropicChatModel:
    def __init__(self, client: anthropic.Anthropic, *, model: str, effort: Effort | None) -> None:
        self._client = client
        self._model = model
        self._effort = effort

    def complete(
        self, *, system: str, messages: Sequence[ChatMessage], max_tokens: int
    ) -> ChatCompletion:
        api_messages = [_to_anthropic_message(message) for message in messages]
        try:
            response = self._client.beta.messages.create(
                model=self._model,
                max_tokens=max_tokens,
                system=system,
                messages=api_messages,
                output_config={"effort": self._effort} if self._effort else anthropic.omit,
                betas=[_FALLBACK_BETA],
                fallbacks="default",
            )
        except anthropic.APIError as error:
            raise to_external_error(error, provider="anthropic", reasons=_ERROR_REASONS) from error

        text = "".join(block.text for block in response.content if isinstance(block, BetaTextBlock))
        return ChatCompletion(
            text=text,
            model=response.model,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            finish_reason=_FINISH_REASONS.get(response.stop_reason or "", "stop"),
        )


def _to_anthropic_message(message: ChatMessage) -> BetaMessageParam:
    if message.role == "user":
        return BetaUserMessageParam(role="user", content=message.content)
    return BetaAssistantMessageParam(role="assistant", content=message.content)
