"""AnthropicChatModel: gerçek `anthropic` SDK'sı + sahte HTTP katmanı (MockTransport)."""

import json
from collections.abc import Callable
from typing import Any

import anthropic
import httpx2
import pytest

from kovan.application.errors import ExternalServiceError
from kovan.application.ports.ai import ChatMessage
from kovan.infrastructure.ai.anthropic_chat import AnthropicChatModel

Handler = Callable[[httpx2.Request], httpx2.Response]


def _model(handler: Handler, *, effort: Any = "low") -> AnthropicChatModel:
    client = anthropic.Anthropic(
        api_key="test-key",
        max_retries=0,
        http_client=httpx2.Client(transport=httpx2.MockTransport(handler)),
    )
    return AnthropicChatModel(client, model="claude-opus-5-5", effort=effort)


def _message_response(text: str, stop_reason: str = "end_turn") -> httpx2.Response:
    return httpx2.Response(
        200,
        json={
            "id": "msg_test",
            "type": "message",
            "role": "assistant",
            "model": "claude-opus-5-5",
            "content": [{"type": "text", "text": text}],
            "stop_reason": stop_reason,
            "stop_sequence": None,
            "usage": {"input_tokens": 120, "output_tokens": 15},
        },
    )


def _ask(model: AnthropicChatModel) -> Any:
    return model.complete(
        system="Sadece bağlamı kullan.",
        messages=[ChatMessage(role="user", content="3NF nedir?")],
        max_tokens=4096,
    )


def test_sends_system_messages_effort_and_server_side_fallback() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx2.Request) -> httpx2.Response:
        captured["body"] = json.loads(request.content)
        captured["beta"] = request.headers.get("anthropic-beta", "")
        return _message_response("Geçişli bağımlılık kaldırılır [1].")

    completion = _ask(_model(handler))

    body = captured["body"]
    assert body["model"] == "claude-opus-5-5"
    assert body["system"] == "Sadece bağlamı kullan."
    assert body["messages"] == [{"role": "user", "content": "3NF nedir?"}]
    assert body["output_config"] == {"effort": "low"}
    assert body["fallbacks"] == "default"
    assert "server-side-fallback-2026-07-01" in captured["beta"]
    assert completion.text == "Geçişli bağımlılık kaldırılır [1]."
    assert (completion.input_tokens, completion.output_tokens) == (120, 15)
    assert completion.finish_reason == "stop"


def test_effort_is_omitted_when_not_configured() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx2.Request) -> httpx2.Response:
        captured["body"] = json.loads(request.content)
        return _message_response("Tamam.")

    _ask(_model(handler, effort=None))

    assert "output_config" not in captured["body"]


@pytest.mark.parametrize(
    ("stop_reason", "expected"), [("refusal", "refusal"), ("max_tokens", "length")]
)
def test_stop_reason_is_mapped(stop_reason: str, expected: str) -> None:
    completion = _ask(_model(lambda _: _message_response("", stop_reason)))

    assert completion.finish_reason == expected


def _error_response(_: httpx2.Request) -> httpx2.Response:
    return httpx2.Response(
        429, json={"type": "error", "error": {"type": "rate_limit_error", "message": "yavaşla"}}
    )


def _connection_failure(request: httpx2.Request) -> httpx2.Response:
    raise httpx2.ConnectError("bağlantı yok", request=request)


@pytest.mark.parametrize("handler", [_error_response, _connection_failure])
def test_provider_failures_become_external_service_error(handler: Handler) -> None:
    with pytest.raises(ExternalServiceError) as error:
        _ask(_model(handler))

    assert error.value.code == "AI_SERVICE_UNAVAILABLE"


def test_conversation_history_keeps_roles() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx2.Request) -> httpx2.Response:
        captured["body"] = json.loads(request.content)
        return _message_response("Tamam.")

    _model(handler).complete(
        system="s",
        messages=[
            ChatMessage("user", "Soru?"),
            ChatMessage("assistant", "Cevap"),
            ChatMessage("user", "Ya bu?"),
        ],
        max_tokens=100,
    )

    assert [m["role"] for m in captured["body"]["messages"]] == ["user", "assistant", "user"]
