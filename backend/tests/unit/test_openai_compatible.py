"""OpenAI uyumlu adaptörler, gerçek `openai` SDK'sı ve sahte bir HTTP katmanı ile test edilir."""

import json
from collections.abc import Callable
from typing import Any

import httpx2
import openai
import pytest

from kovan.application.errors import ExternalServiceError
from kovan.application.ports.ai import ChatMessage
from kovan.infrastructure.ai.openai_compatible import (
    OpenAICompatibleChatModel,
    OpenAICompatibleEmbeddingProvider,
)

Handler = Callable[[httpx2.Request], httpx2.Response]


def _client(handler: Handler) -> openai.OpenAI:
    return openai.OpenAI(
        api_key="test-key",
        base_url="https://ai.example.test/v1",
        max_retries=0,
        http_client=httpx2.Client(transport=httpx2.MockTransport(handler)),
    )


def _embedding_response(request: httpx2.Request, dimension: int) -> httpx2.Response:
    inputs = json.loads(request.content)["input"]
    # Sıranın `index` ile düzeltildiğini görmek için ters sırada döner.
    data = [
        {"object": "embedding", "index": i, "embedding": [float(len(text))] * dimension}
        for i, text in reversed(list(enumerate(inputs)))
    ]
    return httpx2.Response(
        200,
        json={
            "object": "list",
            "model": "m",
            "data": data,
            "usage": {"prompt_tokens": 1, "total_tokens": 1},
        },
    )


def test_embeddings_are_batched_and_returned_in_input_order() -> None:
    requests: list[list[str]] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        requests.append(json.loads(request.content)["input"])
        return _embedding_response(request, dimension=3)

    provider = OpenAICompatibleEmbeddingProvider(
        _client(handler), model="m", dimension=3, batch_size=2
    )

    vectors = provider.embed(["a", "bb", "ccc"])

    assert requests == [["a", "bb"], ["ccc"]]
    assert vectors == [[1.0] * 3, [2.0] * 3, [3.0] * 3]


def test_empty_input_does_not_call_the_api() -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        raise AssertionError("API çağrılmamalıydı")

    provider = OpenAICompatibleEmbeddingProvider(_client(handler), model="m", dimension=3)

    assert provider.embed([]) == []


def test_wrong_vector_dimension_is_reported_as_configuration_error() -> None:
    provider = OpenAICompatibleEmbeddingProvider(
        _client(lambda request: _embedding_response(request, dimension=768)),
        model="m",
        dimension=1536,
    )

    with pytest.raises(ValueError, match="EMBEDDING_DIM=1536"):
        provider.embed(["metin"])


def _chat_response(
    request: httpx2.Request, captured: dict[str, Any], finish: str
) -> httpx2.Response:
    captured["body"] = json.loads(request.content)
    return httpx2.Response(
        200,
        json={
            "id": "c1",
            "object": "chat.completion",
            "created": 0,
            "model": "gpt-test",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "Cevap [1]"},
                    "finish_reason": finish,
                }
            ],
            "usage": {"prompt_tokens": 50, "completion_tokens": 5, "total_tokens": 55},
        },
    )


@pytest.mark.parametrize(("finish", "expected"), [("stop", "stop"), ("content_filter", "refusal")])
def test_chat_sends_system_first_and_maps_the_answer(finish: str, expected: str) -> None:
    captured: dict[str, Any] = {}
    model = OpenAICompatibleChatModel(
        _client(lambda request: _chat_response(request, captured, finish)), model="gpt-test"
    )

    completion = model.complete(
        system="Sadece bağlamı kullan.",
        messages=[ChatMessage("user", "Soru?"), ChatMessage("assistant", "Önceki cevap")],
        max_tokens=300,
    )

    assert captured["body"]["messages"] == [
        {"role": "system", "content": "Sadece bağlamı kullan."},
        {"role": "user", "content": "Soru?"},
        {"role": "assistant", "content": "Önceki cevap"},
    ]
    assert captured["body"]["max_completion_tokens"] == 300
    assert completion.text == "Cevap [1]"
    assert (completion.input_tokens, completion.output_tokens) == (50, 5)
    assert completion.finish_reason == expected


def test_server_error_becomes_external_service_error() -> None:
    provider = OpenAICompatibleEmbeddingProvider(
        _client(lambda _: httpx2.Response(503, json={"error": {"message": "kapalı"}})),
        model="m",
        dimension=3,
    )

    with pytest.raises(ExternalServiceError) as error:
        provider.embed(["metin"])

    assert error.value.code == "AI_SERVICE_UNAVAILABLE"
