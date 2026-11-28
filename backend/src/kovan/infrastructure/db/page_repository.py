"""`PageRepository`'nin PostgreSQL uygulaması (SQLAlchemy Core, ADR-003).

Repository işlem (transaction) açmaz; kendisine verilen bağlantıyı kullanır. İşlemi başlatıp
bitirmek çağıranın işidir (API'de istek başına bir işlem). Böylece testler her şeyi geri
alınan tek bir işlem içinde çalıştırabilir.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any
from uuid import UUID

from sqlalchemy import Connection, Engine, RowMapping, exists, insert, literal, select, update

from kovan.application.ports.pages import PageRef, TreeNode
from kovan.domain.content import PageContent
from kovan.domain.pages import Page, version_conflict
from kovan.infrastructure.db.tables import pages


class SqlPageTransactions:
    """`PageTransactions` port'u: Her `begin()` çağrısı ayrı bir veritabanı işlemi açar."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    @contextmanager
    def begin(self) -> Iterator["SqlPageRepository"]:
        with self._engine.begin() as connection:  # hatasız biterse commit, hata olursa rollback
            yield SqlPageRepository(connection)


class SqlPageRepository:
    def __init__(self, connection: Connection) -> None:
        self._connection = connection

    def add(self, page: Page) -> None:
        self._connection.execute(insert(pages).values(_to_row(page)))

    def get(self, *, owner_id: UUID, page_id: UUID) -> Page | None:
        row = (
            self._connection.execute(
                select(pages).where(
                    pages.c.id == page_id,
                    pages.c.owner_id == owner_id,
                    pages.c.deleted_at.is_(None),
                )
            )
            .mappings()
            .one_or_none()
        )
        return None if row is None else _to_page(row)

    def update(self, page: Page, *, expected_version: int) -> None:
        values = _to_row(page)
        for key in ("id", "owner_id", "created_at"):  # bunlar sayfa oluşturulduktan sonra değişmez
            del values[key]
        result = self._connection.execute(
            update(pages)
            .where(
                pages.c.id == page.id,
                pages.c.owner_id == page.owner_id,
                pages.c.version == expected_version,
            )
            .values(values)
        )
        if result.rowcount == 0:
            raise version_conflict()

    def tree(self, *, owner_id: UUID, limit: int) -> list[TreeNode]:
        child = pages.alias("child")
        has_children = exists().where(child.c.parent_id == pages.c.id, child.c.deleted_at.is_(None))
        rows = self._connection.execute(
            select(pages.c.id, pages.c.parent_id, pages.c.title, has_children.label("has_children"))
            .where(pages.c.owner_id == owner_id, pages.c.deleted_at.is_(None))
            # ICU harmanlaması: Ç, Ğ, I/İ, Ö, Ş, Ü Türkçe alfabedeki yerinde (domain-design § 3).
            .order_by(pages.c.title.collate("tr-x-icu"), pages.c.id)
            .limit(limit)
        )
        return [TreeNode(row.id, row.parent_id, row.title, row.has_children) for row in rows]

    def breadcrumbs(self, *, owner_id: UUID, page_id: UUID) -> list[PageRef]:
        # Özyinelemeli sorgu (recursive CTE): Sayfadan başlayıp `parent_id` ile yukarı çıkar.
        # `depth` 0 sayfanın kendisidir; üst sayfalar en üstteki önce gelecek şekilde sıralanır.
        start = (
            select(pages.c.id, pages.c.parent_id, pages.c.title, literal(0).label("depth"))
            .where(pages.c.id == page_id, pages.c.owner_id == owner_id)
            .cte("ancestors", recursive=True)
        )
        parent = pages.alias("parent")
        ancestors = start.union_all(
            select(parent.c.id, parent.c.parent_id, parent.c.title, start.c.depth + 1).where(
                parent.c.id == start.c.parent_id, parent.c.owner_id == owner_id
            )
        )
        rows = self._connection.execute(
            select(ancestors.c.id, ancestors.c.title)
            .where(ancestors.c.depth > 0)
            .order_by(ancestors.c.depth.desc())
        )
        return [PageRef(id=row.id, title=row.title) for row in rows]


def _to_row(page: Page) -> dict[str, Any]:
    return {
        "id": page.id,
        "owner_id": page.owner_id,
        "parent_id": page.parent_id,
        "title": page.title,
        "content": page.content.blocks,
        "version": page.version,
        "deleted_at": page.deleted_at,
        "indexed_version": page.indexed_version,
        "index_attempts": page.index_attempts,
        "index_error": page.index_error,
        "index_retry_at": page.index_retry_at,
        "created_at": page.created_at,
        "updated_at": page.updated_at,
    }


def _to_page(row: RowMapping) -> Page:
    return Page(
        id=row["id"],
        owner_id=row["owner_id"],
        parent_id=row["parent_id"],
        title=row["title"],
        content=PageContent(row["content"]),
        version=row["version"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        deleted_at=row["deleted_at"],
        indexed_version=row["indexed_version"],
        index_attempts=row["index_attempts"],
        index_error=row["index_error"],
        index_retry_at=row["index_retry_at"],
    )
