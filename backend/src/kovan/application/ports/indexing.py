"""İndeksleme port'ları (ADR-005, ADR-009).

- `PendingPages`: İndekslenmeyi bekleyen sayfalar. PostgreSQL'deki `pages` tablosuyla uygulanır
  (`infrastructure/db/pending_pages.py`); ayrı bir kuyruk tablosu yoktur, bilgi sayfanın kendi
  satırındadır.
- `Chunker`: Sayfayı parçalara bölen fonksiyon (`application/chunking.py`, ADR-009).
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol
from uuid import UUID

from kovan.domain.content import PageContent


@dataclass(frozen=True)
class PageToIndex:
    page_id: UUID
    owner_id: UUID
    title: str
    # Veritabanındaki blok dizisi (JSON). `PageContent`'e servis çevirir: Bozuk bir sayfa yalnızca
    # kendisini "başarısız" yapar, diğer sayfaların okunmasını engellemez.
    content: Any
    version: int
    deleted: bool
    attempts: int  # şimdiye kadarki başarısız deneme sayısı


class PendingPages(Protocol):
    """İndekslenmeyi bekleyen sayfalar (R-10, R-11)."""

    def pages_to_index(
        self, *, now: datetime, settled_before: datetime, limit: int
    ) -> Sequence[PageToIndex]:
        """`indexed_version IS DISTINCT FROM version`, `updated_at ≤ settled_before`,
        `index_attempts < MAX_INDEX_ATTEMPTS` (`domain/pages.py`, R-11) ve yeniden deneme zamanı
        (`index_retry_at`) `now`'a gelmiş sayfalar; en eski düzenlenen önce."""
        ...

    def mark_indexed(self, *, page_id: UUID, version: int) -> None:
        """`indexed_version = version`; deneme sayacı, hata ve bekleme zamanı temizlenir."""
        ...

    def mark_failed(
        self, *, page_id: UUID, version: int, error_code: str, retry_at: datetime
    ) -> None:
        """Deneme sayacı 1 artar; hata kodu ve bir sonraki deneme zamanı yazılır.

        Yalnızca sayfa hâlâ `version` sürümündeyse uygulanır: İndeksleme sürerken sayfa
        düzenlendiyse yeni sürümün sıfırlanmış deneme bilgisi eski sürümün hatasıyla bozulmaz.
        """
        ...


class TextChunk(Protocol):
    """Parçalama fonksiyonunun ürettiği bir parçadan beklenen alanlar.

    Yalnızca alan adları önemlidir; parçalama fonksiyonu kendi veri tipini döndürebilir.
    """

    @property
    def heading_path(self) -> str: ...

    @property
    def text(self) -> str: ...


class Chunker(Protocol):
    def __call__(self, title: str, content: PageContent) -> Sequence[TextChunk]: ...
