"""`PendingPages`'in PostgreSQL uygulaması (ADR-005, R-10, R-11).

Ayrı bir kuyruk tablosu yoktur: Sayfanın indekslenmeyi bekleyip beklemediği kendi satırındaki
`version` ve `indexed_version` alanlarından anlaşılır. Her çağrı kendi işlemini (transaction) açar;
böylece bir sayfanın işaretlenmesi, aynı turdaki diğer sayfaların sonucuna bağlı kalmaz.
İşaretlemeler sayfayı sahibiyle birlikte bulur (`id` ve `owner_id`): Her veri erişimi `owner_id` ile
filtrelenir (AGENTS.md). `updated_at`'e dokunulmaz: O alan kullanıcının son düzenleme zamanıdır.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import Engine, Update, or_, select, update

from kovan.application.ports.indexing import PageToIndex
from kovan.domain.pages import MAX_INDEX_ATTEMPTS
from kovan.infrastructure.db.tables import pages


class SqlPendingPages:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def pages_to_index(
        self, *, now: datetime, settled_before: datetime, limit: int
    ) -> list[PageToIndex]:
        query = (
            select(
                pages.c.id,
                pages.c.owner_id,
                pages.c.title,
                pages.c.content,
                pages.c.version,
                pages.c.deleted_at,
                pages.c.index_attempts,
            )
            .where(
                # R-10. Bu koşul `ix_pages_needs_index` kısmi indeksinin koşuluyla aynıdır; indeks
                # yalnızca bekleyen sayfaları tuttuğu için sorgu sayfa sayısı artsa da hızlı kalır.
                pages.c.indexed_version.is_distinct_from(pages.c.version),
                pages.c.updated_at <= settled_before,  # düzenleme bitti (AC-12.4)
                pages.c.index_attempts < MAX_INDEX_ATTEMPTS,  # R-11: 5 denemeden sonra durur
                or_(pages.c.index_retry_at.is_(None), pages.c.index_retry_at <= now),
            )
            .order_by(pages.c.updated_at)
            .limit(limit)
        )
        with self._engine.connect() as connection:
            rows = connection.execute(query).all()
        return [
            PageToIndex(
                page_id=row.id,
                owner_id=row.owner_id,
                title=row.title,
                content=row.content,
                version=row.version,
                deleted=row.deleted_at is not None,
                attempts=row.index_attempts,
            )
            for row in rows
        ]

    def mark_indexed(self, *, owner_id: UUID, page_id: UUID, version: int) -> None:
        self._execute(
            update(pages)
            .where(pages.c.id == page_id, pages.c.owner_id == owner_id)
            .values(
                indexed_version=version, index_attempts=0, index_error=None, index_retry_at=None
            )
        )

    def mark_failed(
        self, *, owner_id: UUID, page_id: UUID, version: int, error_code: str, retry_at: datetime
    ) -> None:
        # Sürüm koşulu: İndeksleme sürerken sayfa yeniden kaydedildiyse yeni sürümün sıfırlanmış
        # deneme sayacı, eski sürümün hatasıyla bozulmaz.
        self._execute(
            update(pages)
            .where(pages.c.id == page_id, pages.c.owner_id == owner_id, pages.c.version == version)
            .values(
                index_attempts=pages.c.index_attempts + 1,
                index_error=error_code,
                index_retry_at=retry_at,
            )
        )

    def _execute(self, statement: Update) -> None:
        with self._engine.begin() as connection:
            connection.execute(statement)
