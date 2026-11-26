"""QdrantVectorIndex'in gerçek Qdrant sunucusuyla (Testcontainers) çalıştığını doğrular."""

from collections.abc import Iterator
from uuid import uuid4

import pytest
from qdrant_client import QdrantClient
from testcontainers.community.qdrant import QdrantContainer

from kovan.application.ports.vector import VectorPoint
from kovan.infrastructure.vector.qdrant_index import QdrantProbe, QdrantVectorIndex
from tests.integration.containers import require_docker

# İstemci kütüphanesiyle (qdrant-client 1.20) aynı minor sürüm; docker-compose da bunu kullanır.
QDRANT_IMAGE = "qdrant/qdrant:v1.20.2"


@pytest.fixture(scope="module")
def qdrant_client() -> Iterator[QdrantClient]:
    require_docker()
    with QdrantContainer(QDRANT_IMAGE) as qdrant:
        client = qdrant.get_client()
        yield client
        client.close()


@pytest.mark.integration
@pytest.mark.ac("AC-10.2")
def test_real_qdrant_stores_and_filters_by_owner(qdrant_client: QdrantClient) -> None:
    index = QdrantVectorIndex(qdrant_client, dimension=3)
    index.ensure_collection()
    index.ensure_collection()  # ikinci çağrı mevcut koleksiyonu doğrular, hata vermez
    owner, other, page = uuid4(), uuid4(), uuid4()
    point = VectorPoint(chunk_no=0, vector=[1.0, 0.0, 0.0], text="metin", heading_path="Not")

    index.replace_page(
        owner_id=owner, page_id=page, page_title="Not", page_version=1, points=[point]
    )

    assert [hit.page_id for hit in index.search(owner_id=owner, vector=[1, 0, 0], limit=5)] == [
        page
    ]
    assert index.search(owner_id=other, vector=[1, 0, 0], limit=5) == []
    assert QdrantProbe(qdrant_client).is_ready() is True
