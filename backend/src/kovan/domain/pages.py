"""Sayfa (Page) aggregate'i — docs/domain-design.md § 3 ve kurallar R-03, R-07, R-10, R-11.

Sayfa değişmez (frozen) bir nesnedir: Her değişiklik yeni bir `Page` döndürür. Veritabanına
yazma, sahiplik (R-04) ve silme (R-08) `PageService`'in işidir; burada yalnızca sayfanın
kendi kuralları vardır.
"""

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from kovan.domain.content import PageContent
from kovan.domain.errors import ConflictError, DomainRuleError

MAX_TITLE_LENGTH = 200
UNTITLED = "Adsız"
MAX_INDEX_ATTEMPTS = 5  # R-11: 5. başarısız denemeden sonra durum FAILED olur


class IndexStatus(StrEnum):
    """Sayfanın Qdrant'taki durumu (saklanmaz, alanlardan türetilir)."""

    INDEXED = "INDEXED"
    PENDING = "PENDING"
    FAILED = "FAILED"


def normalize_title(raw: str | None) -> str:
    """R-03: Başlık kırpılır; boşsa "Adsız" olur; 200 karakterden uzunsa reddedilir."""
    title = (raw or "").strip()
    if not title:
        return UNTITLED
    if len(title) > MAX_TITLE_LENGTH:
        raise DomainRuleError(
            f"Başlık en fazla {MAX_TITLE_LENGTH} karakter olabilir.",
            rule_code="R-03",
            code="TITLE_TOO_LONG",
        )
    return title


@dataclass(frozen=True)
class Page:
    id: UUID
    owner_id: UUID
    parent_id: UUID | None
    title: str
    content: PageContent
    version: int
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
    indexed_version: int | None = None
    index_attempts: int = 0
    index_error: str | None = None
    index_retry_at: datetime | None = None

    @classmethod
    def create(
        cls,
        *,
        owner_id: UUID,
        parent_id: UUID | None,
        title: str | None,
        content: PageContent,
        now: datetime,
    ) -> "Page":
        """Yeni sayfa: sürüm 1, henüz hiç indekslenmemiş (R-10: `indexed_version` NULL)."""
        return cls(
            id=uuid4(),
            owner_id=owner_id,
            parent_id=parent_id,
            title=normalize_title(title),
            content=content,
            version=1,
            created_at=now,
            updated_at=now,
        )

    def edit(
        self, *, title: str | None, content: PageContent, expected_version: int, now: datetime
    ) -> "Page":
        """Kaydetme (PUT): R-07 sürüm kontrolü, R-10 sürüm artışı, R-11 indeks sayacı sıfırlanır.

        Asıl sürüm kontrolü veritabanında `UPDATE … WHERE version = :beklenen` ile yapılır
        (architecture.md § 5.1); buradaki kontrol aynı kuralın domain'deki karşılığıdır.
        """
        if expected_version != self.version:
            raise version_conflict()
        return replace(
            self,
            title=normalize_title(title),
            content=content,
            version=self.version + 1,
            updated_at=now,
            index_attempts=0,
            index_error=None,
            index_retry_at=None,
        )

    @property
    def index_status(self) -> IndexStatus:
        """domain-design.md § 3: INDEXED, FAILED (≥ 5 başarısız deneme) veya PENDING."""
        if self.indexed_version == self.version:
            return IndexStatus.INDEXED
        if self.index_attempts >= MAX_INDEX_ATTEMPTS:
            return IndexStatus.FAILED
        return IndexStatus.PENDING


def version_conflict() -> ConflictError:
    """R-07 ihlali: İstemcinin sürümü eski (409). Repository de aynı hatayı kullanır."""
    return ConflictError(
        "Bu sayfa başka bir yerde değişti. Sayfayı yenileyip tekrar deneyin.",
        code="VERSION_CONFLICT",
        rule_code="R-07",
    )
