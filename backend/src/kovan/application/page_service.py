"""Sayfa oluşturma ve görüntüleme (US-03, US-05).

R-04: Başkasının, silinmiş ya da olmayan sayfa için hep aynı 404; varlığı belli olmaz (AC-03.4).
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from kovan.application.ports.pages import PageRef, PageRepository, PageTransactions
from kovan.domain.content import PageContent
from kovan.domain.errors import NotFoundError
from kovan.domain.pages import Page

PAGE_NOT_FOUND_MESSAGE = "Sayfa bulunamadı."
PARENT_NOT_FOUND_MESSAGE = "Üst sayfa bulunamadı."


def _utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class PageDetails:
    """Sayfa ve breadcrumb'ı (AC-03.3)."""

    page: Page
    breadcrumbs: list[PageRef]


class PageService:
    def __init__(self, pages: PageTransactions, clock: Callable[[], datetime] = _utc_now) -> None:
        self._pages = pages
        self._clock = clock

    def create(
        self, *, owner_id: UUID, title: str | None, parent_id: UUID | None, content: Any
    ) -> PageDetails:
        """Yeni sayfa açar (AC-03.1); üst sayfa verildiyse kullanıcıya ait olmalı (AC-05.3)."""
        page_content = PageContent([] if content is None else content)  # R-06
        with self._pages.begin() as repository:
            if parent_id is not None:
                _get_owned(repository, owner_id, parent_id, PARENT_NOT_FOUND_MESSAGE)
            page = Page.create(
                owner_id=owner_id,
                parent_id=parent_id,
                title=title,
                content=page_content,
                now=self._clock(),
            )
            repository.add(page)
            return _details(repository, page)

    def get(self, *, owner_id: UUID, page_id: UUID) -> PageDetails:
        """Kullanıcının kendi sayfası; değilse 404 (AC-03.3, AC-03.4)."""
        with self._pages.begin() as repository:
            page = _get_owned(repository, owner_id, page_id, PAGE_NOT_FOUND_MESSAGE)
            return _details(repository, page)


def _get_owned(repository: PageRepository, owner_id: UUID, page_id: UUID, message: str) -> Page:
    page = repository.get(owner_id=owner_id, page_id=page_id)
    if page is None:
        raise NotFoundError(message, code="PAGE_NOT_FOUND")
    return page


def _details(repository: PageRepository, page: Page) -> PageDetails:
    return PageDetails(page, repository.breadcrumbs(owner_id=page.owner_id, page_id=page.id))
