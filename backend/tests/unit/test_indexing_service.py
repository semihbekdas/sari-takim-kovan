"""IndexingService: sahte kuyruk ve parçalayıcı, bellek içi Qdrant ve fake embedding ile."""

from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import pytest
from qdrant_client import QdrantClient

from kovan.application.errors import ExternalServiceError
from kovan.application.indexing_service import UNEXPECTED_ERROR_CODE, IndexingService
from kovan.application.ports.indexing import PageToIndex
from kovan.domain.content import PageContent
from kovan.infrastructure.ai.fake import FakeEmbeddingProvider
from kovan.infrastructure.vector.qdrant_index import DEFAULT_COLLECTION, QdrantVectorIndex

NOW = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
DIM = 64
OWNER = uuid4()


@dataclass
class FakePendingPages:
    """`PendingPages` port'unun test karşılığı: verilen sayfaları döner, işaretlemeleri kaydeder."""

    pages: list[PageToIndex]
    requests: list[tuple[datetime, datetime, int]] = field(default_factory=list)
    indexed: list[tuple[UUID, int]] = field(default_factory=list)
    failed: list[tuple[UUID, int, str, datetime]] = field(default_factory=list)

    def pages_to_index(
        self, *, now: datetime, settled_before: datetime, limit: int
    ) -> Sequence[PageToIndex]:
        self.requests.append((now, settled_before, limit))
        return self.pages[:limit]

    def mark_indexed(self, *, owner_id: UUID, page_id: UUID, version: int) -> None:
        assert owner_id == OWNER
        self.indexed.append((page_id, version))

    def mark_failed(
        self, *, owner_id: UUID, page_id: UUID, version: int, error_code: str, retry_at: datetime
    ) -> None:
        assert owner_id == OWNER
        self.failed.append((page_id, version, error_code, retry_at))


@dataclass(frozen=True)
class Part:
    """Gerçek parçalama fonksiyonunun döndüreceği parçanın yerine geçen test tipi."""

    heading_path: str
    text: str


def split_lines(title: str, content: PageContent) -> Sequence[Part]:
    """Test parçalayıcısı: her paragraf bir parça."""
    lines = content.to_plain_text().splitlines()
    return [Part(heading_path=f"{title} › {i}", text=text) for i, text in enumerate(lines)]


class FailingEmbeddings:
    dimension = DIM

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        raise ExternalServiceError("Ulaşılamıyor.", code="AI_SERVICE_UNAVAILABLE")


class MisconfiguredEmbeddings:
    """Yanlış ayar gibi beklenmeyen bir hata (dış servis hatası değil) fırlatır."""

    dimension = DIM

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        raise ValueError("EMBEDDING_DIM yanlış")


@pytest.fixture
def vector_index() -> Iterator[QdrantVectorIndex]:
    client = QdrantClient(":memory:")
    index = QdrantVectorIndex(client, dimension=DIM)
    index.ensure_collection()
    yield index
    client.close()


def _paragraphs(lines: list[str]) -> list[dict[str, Any]]:
    """Veritabanındaki biçimde içerik: her satır bir paragraf bloğu."""
    return [{"type": "paragraph", "content": [{"type": "text", "text": line}]} for line in lines]


def _page(lines: list[str], *, deleted: bool = False, attempts: int = 0) -> PageToIndex:
    return PageToIndex(
        uuid4(), OWNER, "Not", _paragraphs(lines), version=3, deleted=deleted, attempts=attempts
    )


def _service(
    queue: FakePendingPages,
    index: QdrantVectorIndex,
    embeddings: Any = None,
    *,
    failure_time: datetime = NOW,
) -> IndexingService:
    return IndexingService(
        queue,
        split_lines,
        embeddings or FakeEmbeddingProvider(DIM),
        index,
        settle_seconds=10,
        clock=lambda: failure_time,
    )


def _stored_chunks(index: QdrantVectorIndex) -> list[tuple[UUID, int]]:
    hits = index.search(owner_id=OWNER, vector=[1.0] * DIM, limit=100)
    return sorted((hit.page_id, hit.chunk_no) for hit in hits)


@pytest.mark.ac("AC-12.4")
def test_only_pages_whose_editing_settled_are_requested(vector_index: QdrantVectorIndex) -> None:
    queue = FakePendingPages([])

    _service(queue, vector_index).run_once(NOW)

    assert queue.requests == [(NOW, NOW - timedelta(seconds=10), 10)]


def test_collection_is_created_on_the_first_round() -> None:
    client = QdrantClient(":memory:")
    index = QdrantVectorIndex(client, dimension=DIM)  # koleksiyon henüz yok

    _service(FakePendingPages([]), index).run_once(NOW)

    assert client.collection_exists(DEFAULT_COLLECTION)
    client.close()


def test_page_is_chunked_embedded_stored_and_marked_indexed(
    vector_index: QdrantVectorIndex,
) -> None:
    page = _page(["normalizasyon kuralları", "indeksler hızlandırır"])
    queue = FakePendingPages([page])

    report = _service(queue, vector_index).run_once(NOW)

    assert report.indexed == 1
    assert _stored_chunks(vector_index) == [(page.page_id, 0), (page.page_id, 1)]
    assert queue.indexed == [(page.page_id, 3)]


def test_embedding_text_starts_with_heading_path(vector_index: QdrantVectorIndex) -> None:
    seen: list[str] = []

    class RecordingEmbeddings(FakeEmbeddingProvider):
        def embed(self, texts: Sequence[str]) -> list[list[float]]:
            seen.extend(texts)
            return super().embed(texts)

    _service(FakePendingPages([_page(["3NF"])]), vector_index, RecordingEmbeddings(DIM)).run_once(
        NOW
    )

    assert seen == ["Not › 0\n\n3NF"]


@pytest.mark.ac("AC-06.2")
def test_deleted_page_vectors_are_removed(vector_index: QdrantVectorIndex) -> None:
    page = _page(["eski içerik"])
    _service(FakePendingPages([page]), vector_index).run_once(NOW)
    queue = FakePendingPages([replace(page, deleted=True, version=4)])

    report = _service(queue, vector_index).run_once(NOW)

    assert report.removed == 1
    assert _stored_chunks(vector_index) == []
    assert queue.indexed == [(page.page_id, 4)]


def test_emptied_page_has_no_chunks_left(vector_index: QdrantVectorIndex) -> None:
    page = _page(["bir", "iki"])
    _service(FakePendingPages([page]), vector_index).run_once(NOW)

    _service(FakePendingPages([replace(page, content=[])]), vector_index).run_once(NOW)

    assert _stored_chunks(vector_index) == []


@pytest.mark.ac("AC-12.2")
def test_failure_is_retried_later_with_growing_delay(vector_index: QdrantVectorIndex) -> None:
    page = _page(["metin"], attempts=2)
    queue = FakePendingPages([page])

    report = _service(queue, vector_index, FailingEmbeddings()).run_once(NOW)

    assert report.failed == 1
    assert queue.indexed == []
    assert queue.failed == [
        (page.page_id, 3, "AI_SERVICE_UNAVAILABLE", NOW + timedelta(seconds=20))
    ]


def test_one_failing_page_does_not_stop_the_others(vector_index: QdrantVectorIndex) -> None:
    deleted = _page(["x"], deleted=True)
    failing = _page(["y"])
    queue = FakePendingPages([failing, deleted])

    report = _service(queue, vector_index, FailingEmbeddings()).run_once(NOW)

    assert (report.failed, report.removed) == (1, 1)
    assert queue.indexed == [(deleted.page_id, 3)]


def test_unexpected_error_marks_the_page_failed_and_others_continue(
    vector_index: QdrantVectorIndex,
) -> None:
    # Hata yutulsaydı sayfa işaretlenmez, her turda (ücretli çağrıyla) sonsuza kadar denenirdi.
    failing = _page(["metin"], attempts=1)
    deleted = _page(["x"], deleted=True)
    queue = FakePendingPages([failing, deleted])

    report = _service(queue, vector_index, MisconfiguredEmbeddings()).run_once(NOW)

    assert queue.failed == [
        (failing.page_id, 3, UNEXPECTED_ERROR_CODE, NOW + timedelta(seconds=10))
    ]
    assert queue.indexed == [(deleted.page_id, 3)]
    assert (report.failed, report.removed) == (1, 1)
    assert [str(error) for error in report.unexpected_errors] == ["EMBEDDING_DIM yanlış"]


def test_retry_delay_counts_from_the_moment_of_failure(vector_index: QdrantVectorIndex) -> None:
    # Embedding isteği 60 sn zaman aşımına uğradıysa bekleme turun başından değil hatadan sayılır.
    page = _page(["metin"], attempts=2)
    queue = FakePendingPages([page])
    failed_at = NOW + timedelta(seconds=60)

    _service(queue, vector_index, FailingEmbeddings(), failure_time=failed_at).run_once(NOW)

    assert queue.failed[0][3] == failed_at + timedelta(seconds=20)


def test_page_with_invalid_stored_content_fails_alone(vector_index: QdrantVectorIndex) -> None:
    # Kurallar sonradan sıkılaşırsa eski bir sayfa artık geçersiz olabilir (R-06). O sayfa
    # "başarısız" işaretlenir; turdaki diğer sayfalar işlenmeye devam eder.
    broken = replace(_page([]), content=[{"type": "table"}])
    healthy = _page(["metin"])
    queue = FakePendingPages([broken, healthy])

    report = _service(queue, vector_index).run_once(NOW)

    assert [(page_id, code) for page_id, _, code, _ in queue.failed] == [
        (broken.page_id, UNEXPECTED_ERROR_CODE)
    ]
    assert queue.indexed == [(healthy.page_id, 3)]
    assert report.indexed == 1
