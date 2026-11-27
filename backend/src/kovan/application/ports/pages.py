"""Sayfa deposu port'ları (domain-design.md § 3, architecture.md § 5.1).

Her işlem `owner_id` ile yapılır: Bir kullanıcı başkasının sayfasını göremez, değiştiremez (R-04).
"""

from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from kovan.domain.pages import Page


@dataclass(frozen=True)
class PageRef:
    """Breadcrumb'daki bir üst sayfa."""

    id: UUID
    title: str


class PageRepository(Protocol):
    def add(self, page: Page) -> None:
        """Yeni sayfayı kaydeder."""
        ...

    def get(self, *, owner_id: UUID, page_id: UUID) -> Page | None:
        """Kullanıcının silinmemiş sayfası; yoksa, başkasınınsa ya da silinmişse `None`."""
        ...

    def update(self, page: Page, *, expected_version: int) -> None:
        """Sayfayı yalnızca veritabanındaki sürüm hâlâ `expected_version` ise yazar (R-07).

        Sürüm değişmişse (ör. başka bir sekmede kaydedildiyse) `ConflictError` fırlatır.
        Kontrol `UPDATE … WHERE version = :beklenen` ile tek adımda yapılır; böylece aynı anda
        gelen iki kayıttan yalnızca biri geçer.
        """
        ...

    def breadcrumbs(self, *, owner_id: UUID, page_id: UUID) -> list[PageRef]:
        """Üst sayfalar, en üstteki önce (AC-05.2); sayfanın kendisi listede yoktur."""
        ...


class PageTransactions(Protocol):
    def begin(self) -> AbstractContextManager[PageRepository]:
        """Bir veritabanı işlemi açar: `with` bloğu hatasız biterse commit, hata olursa rollback."""
        ...
