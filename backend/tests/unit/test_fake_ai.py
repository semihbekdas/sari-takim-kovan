import math

from kovan.application.ports.ai import ChatMessage
from kovan.infrastructure.ai.fake import DEFAULT_FAKE_REPLY, FakeChatModel, FakeEmbeddingProvider


def _cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


def test_fake_embedding_is_deterministic_normalized_and_sized() -> None:
    provider = FakeEmbeddingProvider(dimension=64)

    first, second = provider.embed(["Veritabanı normalizasyonu", "Veritabanı normalizasyonu"])

    assert first == second
    assert len(first) == 64
    assert math.isclose(math.sqrt(sum(v * v for v in first)), 1.0)


def test_texts_sharing_words_are_closer_than_unrelated_texts() -> None:
    provider = FakeEmbeddingProvider(dimension=256)
    query, related, unrelated = provider.embed(
        ["normalizasyon kuralları", "3NF normalizasyon kuralları özeti", "mercimek çorbası tarifi"]
    )

    assert _cosine(query, related) > _cosine(query, unrelated)


def test_empty_text_gives_zero_vector() -> None:
    assert FakeEmbeddingProvider(dimension=8).embed([""]) == [[0.0] * 8]


def test_fake_chat_returns_reply_and_records_the_prompt() -> None:
    model = FakeChatModel()

    completion = model.complete(
        system="Sadece bağlamı kullan.",
        messages=[ChatMessage(role="user", content="3NF nedir?")],
        max_tokens=100,
    )

    assert completion.text == DEFAULT_FAKE_REPLY
    assert completion.model == "fake"
    assert completion.finish_reason == "stop"
    assert model.calls == [("Sadece bağlamı kullan.", (ChatMessage("user", "3NF nedir?"),))]
