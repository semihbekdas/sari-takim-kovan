"""QdrantVectorIndex, Docker gerektirmeyen bellek içi Qdrant ile test edilir.

Gerçek Qdrant sunucusuyla temel akış ayrıca doğrulanır: tests/integration/test_qdrant_server.py
"""

from collections.abc import Callable, Iterator
from typing import Any, NoReturn
from uuid import UUID, uuid4

import httpx
import pytest
from qdrant_client import QdrantClient, models
from qdrant_client.common.client_exceptions import ResourceExhaustedResponse
from qdrant_client.http.exceptions import UnexpectedResponse

from kovan.application.errors import ExternalServiceError
from kovan.application.ports.vector import VectorPoint
from kovan.infrastructure.vector.qdrant_index import QdrantProbe, QdrantVectorIndex, point_id
from tests.fakes import UNREACHABLE_QDRANT_URL

DIM = 4
AYSE, MEHMET = uuid4(), uuid4()


@pytest.fixture
def index() -> Iterator[QdrantVectorIndex]:
    client = QdrantClient(":memory:")
    vector_index = QdrantVectorIndex(client, dimension=DIM)
    vector_index.ensure_collection()
    yield vector_index
    client.close()


def _points(*vectors: list[float]) -> list[VectorPoint]:
    return [
        VectorPoint(chunk_no=i, vector=v, text=f"parça {i}", heading_path=f"Not › Bölüm {i}")
        for i, v in enumerate(vectors)
    ]


def _write(index: QdrantVectorIndex, owner: UUID, page: UUID, *vectors: list[float]) -> None:
    index.replace_page(
        owner_id=owner, page_id=page, page_title="Not", page_version=1, points=_points(*vectors)
    )


def _all_hits(index: QdrantVectorIndex, owner: UUID) -> list[tuple[UUID, int]]:
    hits = index.search(owner_id=owner, vector=[1.0, 1.0, 1.0, 1.0], limit=100)
    return sorted((hit.page_id, hit.chunk_no) for hit in hits)


def test_search_returns_nearest_chunk_with_its_details(index: QdrantVectorIndex) -> None:
    page = uuid4()
    _write(index, AYSE, page, [1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0])

    hits = index.search(owner_id=AYSE, vector=[0.9, 0.1, 0.0, 0.0], limit=1)

    assert len(hits) == 1
    assert (hits[0].page_id, hits[0].chunk_no) == (page, 0)
    assert hits[0].text == "parça 0"
    assert hits[0].heading_path == "Not › Bölüm 0"
    assert hits[0].page_title == "Not"


@pytest.mark.ac("AC-10.2")
def test_search_never_returns_other_users_chunks(index: QdrantVectorIndex) -> None:
    ayse_page, mehmet_page = uuid4(), uuid4()
    _write(index, AYSE, ayse_page, [1.0, 0.0, 0.0, 0.0])
    _write(index, MEHMET, mehmet_page, [1.0, 0.0, 0.0, 0.0])  # aynı içerik, başka kullanıcı

    assert _all_hits(index, AYSE) == [(ayse_page, 0)]
    assert _all_hits(index, MEHMET) == [(mehmet_page, 0)]


@pytest.mark.ac("AC-12.3")
def test_writing_the_same_page_twice_is_idempotent(index: QdrantVectorIndex) -> None:
    page = uuid4()
    _write(index, AYSE, page, [1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0])
    _write(index, AYSE, page, [1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0])

    assert _all_hits(index, AYSE) == [(page, 0), (page, 1)]


@pytest.mark.ac("AC-12.5")
def test_shrinking_content_removes_stale_chunks(index: QdrantVectorIndex) -> None:
    page = uuid4()
    _write(index, AYSE, page, *([[1.0, 0.0, 0.0, 0.0]] * 5))
    _write(index, AYSE, page, *([[1.0, 0.0, 0.0, 0.0]] * 2))

    assert _all_hits(index, AYSE) == [(page, 0), (page, 1)]


@pytest.mark.ac("AC-06.2")
def test_delete_page_removes_only_that_page(index: QdrantVectorIndex) -> None:
    deleted, kept = uuid4(), uuid4()
    _write(index, AYSE, deleted, [1.0, 0.0, 0.0, 0.0])
    _write(index, AYSE, kept, [0.0, 1.0, 0.0, 0.0])

    index.delete_page(page_id=deleted)

    assert _all_hits(index, AYSE) == [(kept, 0)]


def test_point_id_is_deterministic_per_page_and_chunk() -> None:
    page = uuid4()

    assert point_id(page, 0) == point_id(page, 0)
    assert point_id(page, 0) != point_id(page, 1)
    assert point_id(page, 0) != point_id(uuid4(), 0)


def test_existing_collection_with_wrong_dimension_is_reported() -> None:
    client = QdrantClient(":memory:")
    QdrantVectorIndex(client, dimension=DIM).ensure_collection()

    with pytest.raises(ValueError, match="EMBEDDING_DIM=8"):
        QdrantVectorIndex(client, dimension=8).ensure_collection()


@pytest.fixture
def unreachable() -> Iterator[QdrantClient]:
    client = QdrantClient(url=UNREACHABLE_QDRANT_URL, timeout=2, check_compatibility=False)
    yield client
    client.close()


@pytest.mark.parametrize(
    "operation",
    [
        lambda index: index.ensure_collection(),
        lambda index: index.search(owner_id=AYSE, vector=[1.0] * DIM, limit=5),
        lambda index: index.delete_page(page_id=uuid4()),
        lambda index: _write(index, AYSE, uuid4(), [1.0, 0.0, 0.0, 0.0]),
    ],
)
def test_unreachable_qdrant_becomes_external_service_error(
    unreachable: QdrantClient, operation: Callable[[QdrantVectorIndex], object]
) -> None:
    with pytest.raises(ExternalServiceError) as error:
        operation(QdrantVectorIndex(unreachable, dimension=DIM))

    assert error.value.code == "VECTOR_STORE_UNAVAILABLE"


def test_probe_reports_unreachable_qdrant_as_down(unreachable: QdrantClient) -> None:
    assert QdrantProbe(unreachable).is_ready() is False


def test_probe_reports_reachable_qdrant_as_up() -> None:
    assert QdrantProbe(QdrantClient(":memory:")).is_ready() is True


class _RateLimitedClient(QdrantClient):
    """Her istekte Qdrant'ın 429 ("kaynak tükendi") hatasını fırlatan istemci."""

    def query_points(self, *args: Any, **kwargs: Any) -> NoReturn:
        raise ResourceExhaustedResponse("Çok fazla istek", retry_after_s=1)

    def get_collections(self, *args: Any, **kwargs: Any) -> NoReturn:
        raise ResourceExhaustedResponse("Çok fazla istek", retry_after_s=1)


def test_rate_limited_qdrant_becomes_unavailable_not_a_crash() -> None:
    client = _RateLimitedClient(":memory:")

    with pytest.raises(ExternalServiceError) as error:
        QdrantVectorIndex(client, dimension=DIM).search(owner_id=AYSE, vector=[1.0] * DIM, limit=5)

    assert error.value.code == "VECTOR_STORE_UNAVAILABLE"
    assert QdrantProbe(client).is_ready() is False


def _http_error(status: int) -> UnexpectedResponse:
    return UnexpectedResponse(status, "hata", b"", httpx.Headers())


class _FlakyClient(QdrantClient):
    """İstenince yazmayı (upsert) geçici bir hatayla başarısız kılan bellek içi istemci."""

    fail_writes = False

    def upsert(self, *args: Any, **kwargs: Any) -> Any:
        if self.fail_writes:
            raise ResourceExhaustedResponse("Çok fazla istek", retry_after_s=1)
        return super().upsert(*args, **kwargs)


def test_failed_rewrite_keeps_the_old_chunks_searchable() -> None:
    client = _FlakyClient(":memory:")
    index = QdrantVectorIndex(client, dimension=DIM)
    index.ensure_collection()
    page = uuid4()
    _write(index, AYSE, page, [1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0])

    client.fail_writes = True
    with pytest.raises(ExternalServiceError):
        _write(index, AYSE, page, [0.0, 0.0, 1.0, 0.0])

    assert _all_hits(index, AYSE) == [(page, 0), (page, 1)]


class _MissingCollectionClient(QdrantClient):
    def query_points(self, *args: Any, **kwargs: Any) -> NoReturn:
        raise _http_error(404)


def test_permanent_error_is_not_reported_as_a_temporary_outage() -> None:
    # 404 (koleksiyon yok) yeniden denemeyle düzelmez; "servis şu an yok" (503) denmemeli.
    index = QdrantVectorIndex(_MissingCollectionClient(":memory:"), dimension=DIM)

    with pytest.raises(UnexpectedResponse):
        index.search(owner_id=AYSE, vector=[1.0] * DIM, limit=5)


class _RacingClient(QdrantClient):
    """Koleksiyonu oluşturur ama başka bir süreç önce davranmış gibi 409 döner."""

    def create_collection(self, *args: Any, **kwargs: Any) -> NoReturn:
        super().create_collection(*args, **kwargs)
        raise _http_error(409)


def test_collection_created_by_another_process_at_the_same_time_is_fine() -> None:
    client = _RacingClient(":memory:")

    QdrantVectorIndex(client, dimension=DIM).ensure_collection()

    assert client.collection_exists("page_chunks")


class _IndexRecordingClient(QdrantClient):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.indexed_fields: list[str] = []

    def create_payload_index(self, *args: Any, **kwargs: Any) -> Any:
        self.indexed_fields.append(kwargs["field_name"])
        return super().create_payload_index(*args, **kwargs)


def test_payload_indexes_are_completed_even_if_the_collection_exists() -> None:
    # Önceki bir açılışta indeks oluşturulurken kesinti olduysa bir sonraki açılış onarır.
    client = _IndexRecordingClient(":memory:")
    client.create_collection(
        "page_chunks",
        vectors_config=models.VectorParams(size=DIM, distance=models.Distance.COSINE),
    )

    QdrantVectorIndex(client, dimension=DIM).ensure_collection()

    assert client.indexed_fields == ["owner_id", "page_id"]
