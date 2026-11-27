"""Vektör indeksi port'u (ADR-004, ADR-005).

Qdrant türetilmiş bir indekstir; kaynak veri PostgreSQL'dedir.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True)
class VectorPoint:
    """Bir sayfa parçasının (chunk) indekse yazılacak hali."""

    chunk_no: int
    vector: Sequence[float]
    text: str
    heading_path: str


@dataclass(frozen=True)
class VectorHit:
    """Aramada bulunan bir parça."""

    page_id: UUID
    chunk_no: int
    score: float
    text: str
    heading_path: str
    page_title: str


class VectorIndex(Protocol):
    def ensure_collection(self) -> None:
        """Koleksiyon yoksa oluşturur, varsa boyutunu doğrular. Tekrar çağrılabilir."""
        ...

    def replace_page(
        self,
        *,
        owner_id: UUID,
        page_id: UUID,
        page_title: str,
        page_version: int,
        points: Sequence[VectorPoint],
    ) -> None:
        """Sayfanın eski noktalarını siler, yenilerini yazar. Aynı veriyle tekrar çağrılabilir."""
        ...

    def delete_page(self, *, page_id: UUID) -> None:
        """Sayfaya ait bütün noktaları siler."""
        ...

    def search(self, *, owner_id: UUID, vector: Sequence[float], limit: int) -> list[VectorHit]:
        """Yalnızca `owner_id` kullanıcısının noktalarında arar (R-12)."""
        ...
