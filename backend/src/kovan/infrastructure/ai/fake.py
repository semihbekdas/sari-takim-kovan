"""API anahtarı gerektirmeyen sahte (fake) sağlayıcılar.

Hem testlerde hem de uygulamanın varsayılan "fake" modunda kullanılır: İnternete çıkmaz,
para harcamaz ve her zaman aynı sonucu verir (deterministik).
"""

import hashlib
import math
import re
from collections.abc import Sequence
from dataclasses import dataclass, field

from kovan.application.ports.ai import ChatCompletion, ChatMessage

_WORD = re.compile(r"\w+", re.UNICODE)

FAKE_MODEL_NAME = "fake"
# Fake modda uygulama uzun süre çalışabilir; kaydedilen çağrılar sınırsız büyümesin.
MAX_RECORDED_CALLS = 20
DEFAULT_FAKE_REPLY = "Bu cevap fake modda üretildi; gerçek bir dil modeli kullanılmadı. [1]"


class FakeEmbeddingProvider:
    """Kelime tabanlı deterministik vektörler: Ortak kelimesi çok olan metinler yakın çıkar.

    Anlam bilmez ("araba" ile "otomobil"i eşleştiremez); gerçek anlamsal kalite RAG
    değerlendirme setinde gerçek modelle ölçülür.
    """

    def __init__(self, dimension: int = 256) -> None:
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        vector = [0.0] * self._dimension
        # "İ".lower() "i" + birleşik nokta verir ve kelimeyi ikiye böler; önce düz "i" yapılır.
        for word in _WORD.findall(text.replace("İ", "i").lower()):
            digest = hashlib.blake2b(word.encode("utf-8"), digest_size=8).digest()
            vector[int.from_bytes(digest, "big") % self._dimension] += 1.0
        norm = math.sqrt(sum(value * value for value in vector))
        return [value / norm for value in vector] if norm else vector


@dataclass
class FakeChatModel:
    """Her zaman verilen cevabı döner; son çağrıları saklar (testte prompt doğrulamak için)."""

    reply: str = DEFAULT_FAKE_REPLY
    calls: list[tuple[str, tuple[ChatMessage, ...]]] = field(default_factory=list)

    def complete(
        self, *, system: str, messages: Sequence[ChatMessage], max_tokens: int
    ) -> ChatCompletion:
        self.calls.append((system, tuple(messages)))
        del self.calls[:-MAX_RECORDED_CALLS]
        input_words = len(system.split()) + sum(len(m.content.split()) for m in messages)
        return ChatCompletion(
            text=self.reply,
            model=FAKE_MODEL_NAME,
            input_tokens=input_words,
            output_tokens=len(self.reply.split()),
        )
