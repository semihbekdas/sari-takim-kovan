"""İndeksleme uçtan uca (#15; ADR-005): Sayfa gerçek PostgreSQL'e kaydedilir, `SqlPendingPages`
bekleyenleri bulur, gerçek parçalama fonksiyonu böler, parçalar bellek içi Qdrant'a yazılır.

Embedding sahtedir (fake): Kaç kez ve hangi metinle çağrıldığı sayılır. Zaman elle ilerletilir.
"""

from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from functools import partial
from typing import Any
from uuid import UUID, uuid4

import pytest
from qdrant_client import QdrantClient
from sqlalchemy import Engine, insert, select, update

from kovan.application.chunking import chunk_page
from kovan.application.errors import ExternalServiceError
from kovan.application.indexing_service import IndexingService
from kovan.application.page_service import PageService
from kovan.domain.pages import MAX_INDEX_ATTEMPTS, IndexStatus, Page
from kovan.infrastructure.ai.fake import FakeEmbeddingProvider
from kovan.infrastructure.db.page_repository import SqlPageTransactions
from kovan.infrastructure.db.pending_pages import SqlPendingPages
from kovan.infrastructure.db.tables import pages, users
from kovan.infrastructure.vector.qdrant_index import QdrantVectorIndex

pytestmark = pytest.mark.integration

T0 = datetime(2026, 11, 27, 12, 0, tzinfo=UTC)
SETTLE = timedelta(seconds=10)
DIM = 64


def paragraph(text: str) -> dict[str, Any]:
    return {"type": "paragraph", "content": [{"type": "text", "text": text}]}


@dataclass
class Clock:
    now: datetime = T0

    def __call__(self) -> datetime:
        return self.now


class CountingEmbeddings(FakeEmbeddingProvider):
    def __init__(self) -> None:
        super().__init__(dimension=DIM)
        self.calls: list[list[str]] = []

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        self.calls.append(list(texts))
        return super().embed(texts)


class FailingEmbeddings:
    dimension = DIM

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        raise ExternalServiceError("Ulaşılamıyor.", code="AI_SERVICE_UNAVAILABLE")


@pytest.fixture
def owner(clean_users: Engine) -> UUID:
    user_id = uuid4()
    with clean_users.begin() as connection:
        connection.execute(
            insert(users).values(
                id=user_id, email="ayse@ornek.com", display_name="Ayşe", password_hash="$test"
            )
        )
    return user_id


@pytest.fixture
def vector_index() -> Iterator[QdrantVectorIndex]:
    client = QdrantClient(":memory:")
    yield QdrantVectorIndex(client, dimension=DIM)
    client.close()


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
def page_service(db_engine: Engine, clock: Clock) -> PageService:
    return PageService(SqlPageTransactions(db_engine), clock=clock)


def indexer(
    engine: Engine, index: QdrantVectorIndex, embeddings: Any, clock: Clock
) -> IndexingService:
    return IndexingService(
        SqlPendingPages(engine),
        partial(chunk_page, max_chars=1000),
        embeddings,
        index,
        settle_seconds=int(SETTLE.total_seconds()),
        clock=clock,
    )


def new_page(service: PageService, owner: UUID, title: str, text: str) -> Page:
    details = service.create(owner_id=owner, title=title, parent_id=None, content=[paragraph(text)])
    return details.page


def stored_page_ids(index: QdrantVectorIndex, owner: UUID) -> list[UUID]:
    return [hit.page_id for hit in index.search(owner_id=owner, vector=[1.0] * DIM, limit=100)]


def test_saved_page_is_indexed_after_settle_and_found_by_search(
    db_engine: Engine,
    owner: UUID,
    page_service: PageService,
    vector_index: QdrantVectorIndex,
    clock: Clock,
) -> None:
    page = new_page(page_service, owner, "Veritabanı", "3NF geçişli bağımlılığı kaldırır")

    report = indexer(db_engine, vector_index, CountingEmbeddings(), clock).run_once(T0 + SETTLE)

    assert report.indexed == 1
    saved = page_service.get(owner_id=owner, page_id=page.id).page
    assert saved.index_status is IndexStatus.INDEXED
    hits = vector_index.search(owner_id=owner, vector=[1.0] * DIM, limit=10)
    assert [(hit.page_id, hit.heading_path, hit.text) for hit in hits] == [
        (page.id, "Veritabanı", "3NF geçişli bağımlılığı kaldırır")
    ]


@pytest.mark.ac("AC-12.4")
def test_rapid_saves_trigger_single_embedding_call_after_settle(
    db_engine: Engine,
    owner: UUID,
    page_service: PageService,
    vector_index: QdrantVectorIndex,
    clock: Clock,
) -> None:
    page = new_page(page_service, owner, "Taslak", "sürüm 1")
    for version in range(1, 5):  # 4 otomatik kayıt, saniyede bir
        clock.now += timedelta(seconds=1)
        page_service.update(
            owner_id=owner,
            page_id=page.id,
            title="Taslak",
            content=[paragraph(f"sürüm {version + 1}")],
            version=version,
        )
    last_save = clock.now
    embeddings = CountingEmbeddings()
    service = indexer(db_engine, vector_index, embeddings, clock)

    service.run_once(last_save + SETTLE - timedelta(seconds=1))  # düzenleme henüz durmadı
    assert embeddings.calls == []

    service.run_once(last_save + SETTLE)
    service.run_once(last_save + SETTLE + timedelta(minutes=1))  # zaten indekslendi

    assert embeddings.calls == [["Taslak\n\nsürüm 5"]]  # yalnızca son sürüm, bir kez


@pytest.mark.ac("AC-12.2")
def test_failed_indexing_retried_with_backoff_then_marked_failed(
    db_engine: Engine,
    owner: UUID,
    page_service: PageService,
    vector_index: QdrantVectorIndex,
    clock: Clock,
) -> None:
    page = new_page(page_service, owner, "Not", "metin")
    service = indexer(db_engine, vector_index, FailingEmbeddings(), clock)
    now = T0 + SETTLE

    for delay in (5, 10, 20, 40, 80):  # R-11: 5 × 2^n saniye
        clock.now = now
        assert service.run_once(now).failed == 1
        assert service.run_once(now + timedelta(seconds=delay - 1)).failed == 0  # erken
        now += timedelta(seconds=delay)

    failed = page_service.get(owner_id=owner, page_id=page.id).page
    assert (failed.index_attempts, failed.index_status) == (MAX_INDEX_ATTEMPTS, IndexStatus.FAILED)
    assert service.run_once(now + timedelta(days=1)).failed == 0  # artık denenmez

    edited = page_service.update(
        owner_id=owner, page_id=page.id, title="Not", content=[paragraph("yeni")], version=1
    ).page
    assert (edited.index_attempts, edited.index_status) == (0, IndexStatus.PENDING)


@pytest.mark.ac("AC-06.2")
def test_deleted_page_vectors_removed_by_index_loop(
    db_engine: Engine,
    owner: UUID,
    page_service: PageService,
    vector_index: QdrantVectorIndex,
    clock: Clock,
) -> None:
    page = new_page(page_service, owner, "Eski", "silinecek not")
    service = indexer(db_engine, vector_index, CountingEmbeddings(), clock)
    service.run_once(T0 + SETTLE)
    assert stored_page_ids(vector_index, owner) == [page.id]

    # Silme uç noktası henüz yok (US-06). Silme, R-08 ve R-10'a göre veritabanında böyle görünür.
    deleted_at = T0 + timedelta(minutes=1)
    with db_engine.begin() as connection:
        connection.execute(
            update(pages)
            .where(pages.c.id == page.id)
            .values(deleted_at=deleted_at, updated_at=deleted_at, version=pages.c.version + 1)
        )

    report = service.run_once(deleted_at + SETTLE)

    assert report.removed == 1
    assert stored_page_ids(vector_index, owner) == []
    with db_engine.connect() as connection:
        indexed_version = connection.scalar(
            select(pages.c.indexed_version).where(pages.c.id == page.id)
        )
    assert indexed_version == 2


def test_failure_of_an_old_version_does_not_touch_the_new_version(
    db_engine: Engine, owner: UUID, page_service: PageService
) -> None:
    page = new_page(page_service, owner, "Not", "sürüm 1")
    page_service.update(
        owner_id=owner, page_id=page.id, title="Not", content=[paragraph("sürüm 2")], version=1
    )

    # Sürüm 1'in indekslemesi, sayfa sürüm 2'ye kaydedildikten sonra hata verdi.
    SqlPendingPages(db_engine).mark_failed(
        owner_id=owner, page_id=page.id, version=1, error_code="AI_SERVICE_UNAVAILABLE", retry_at=T0
    )

    current = page_service.get(owner_id=owner, page_id=page.id).page
    assert (current.version, current.index_attempts, current.index_error) == (2, 0, None)


def test_index_state_is_written_only_with_the_pages_owner(
    db_engine: Engine, owner: UUID, page_service: PageService
) -> None:
    page = new_page(page_service, owner, "Not", "metin")
    pending = SqlPendingPages(db_engine)
    stranger = uuid4()

    pending.mark_indexed(owner_id=stranger, page_id=page.id, version=1)
    pending.mark_failed(owner_id=stranger, page_id=page.id, version=1, error_code="X", retry_at=T0)

    unchanged = page_service.get(owner_id=owner, page_id=page.id).page
    assert (unchanged.indexed_version, unchanged.index_attempts) == (None, 0)
