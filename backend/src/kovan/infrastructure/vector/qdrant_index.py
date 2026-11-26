"""Qdrant ile `VectorIndex` uygulaması ve hazırlık kontrolü (ADR-004, ADR-005).

- Tek koleksiyon (`page_chunks`), kosinüs benzerliği.
- Nokta kimliği deterministik: aynı sayfa + aynı parça numarası → aynı kimlik (idempotent yazma).
- Her arama `owner_id` ile filtrelenir: Bir kullanıcı başkasının notlarını asla göremez (R-12).
"""

from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from typing import Any
from uuid import NAMESPACE_DNS, UUID, uuid5

import structlog
from qdrant_client import QdrantClient, models
from qdrant_client.common.client_exceptions import QdrantException
from qdrant_client.http.exceptions import ApiException, UnexpectedResponse

from kovan.application.errors import ExternalServiceError
from kovan.application.ports.vector import VectorHit, VectorPoint

DEFAULT_COLLECTION = "page_chunks"
VECTOR_STORE_UNAVAILABLE = "VECTOR_STORE_UNAVAILABLE"

_POINT_NAMESPACE = uuid5(NAMESPACE_DNS, "kovan.page-chunks")

logger = structlog.get_logger(__name__)

# Qdrant'ın HTTP hataları `ApiException`'dan, istemci tarafı hataları (ör. 429 "kaynak tükendi")
# `QdrantException`'dan türer; ikisi de "Qdrant'a şu an ulaşılamıyor" demektir.
QDRANT_ERRORS = (ApiException, QdrantException)
CONFLICT, TOO_MANY_REQUESTS, SERVER_ERROR = 409, 429, 500


def point_id(page_id: UUID, chunk_no: int) -> str:
    """Aynı sayfa ve parça için her zaman aynı kimliği üretir."""
    return str(uuid5(_POINT_NAMESPACE, f"{page_id}:{chunk_no}"))


class QdrantVectorIndex:
    def __init__(
        self, client: QdrantClient, *, dimension: int, collection: str = DEFAULT_COLLECTION
    ) -> None:
        self._client = client
        self._dimension = dimension
        self._collection = collection

    def ensure_collection(self) -> None:
        """Koleksiyon yoksa oluşturur, boyutunun ayarlarla aynı olduğunu doğrular.

        Payload indeksleri her seferinde tamamlanır (Qdrant'ta tekrar oluşturmak zararsızdır);
        böylece yarım kalmış bir kurulum bir sonraki açılışta kendiliğinden onarılır.
        """
        with _translate_errors():
            if not self._client.collection_exists(self._collection):
                self._create_collection()
            self._check_dimension()
            for field in ("owner_id", "page_id"):
                self._client.create_payload_index(
                    self._collection,
                    field_name=field,
                    field_schema=models.PayloadSchemaType.KEYWORD,
                )

    def _create_collection(self) -> None:
        try:
            self._client.create_collection(
                self._collection,
                vectors_config=models.VectorParams(
                    size=self._dimension, distance=models.Distance.COSINE
                ),
            )
        except UnexpectedResponse as error:
            # 409: Aynı anda başka bir süreç (ör. ikinci worker) koleksiyonu oluşturdu; sorun yok.
            if error.status_code != CONFLICT:
                raise

    def replace_page(
        self,
        *,
        owner_id: UUID,
        page_id: UUID,
        page_title: str,
        page_version: int,
        points: Sequence[VectorPoint],
    ) -> None:
        payload = {
            "owner_id": str(owner_id),
            "page_id": str(page_id),
            "page_title": page_title,
            "page_version": page_version,
        }
        structs = [
            models.PointStruct(
                id=point_id(page_id, point.chunk_no),
                vector=list(point.vector),
                payload={
                    **payload,
                    "chunk_no": point.chunk_no,
                    "text": point.text,
                    "heading_path": point.heading_path,
                },
            )
            for point in points
        ]
        with _translate_errors():
            # Önce yeni parçalar yazılır (kimlikler deterministik olduğu için aynı numaralı parça
            # üzerine yazılır), sonra artık olmayan parçalar silinir. Yazma başarısız olursa
            # sayfanın eski hâli aranabilir kalır. `chunk_no` 0'dan başlayan ardışık sayılardır.
            if structs:
                self._client.upsert(self._collection, points=structs, wait=True)
            self._delete(_match("page_id", page_id, chunk_no_from=len(structs)))

    def delete_page(self, *, page_id: UUID) -> None:
        with _translate_errors():
            self._delete(_match("page_id", page_id))

    def search(self, *, owner_id: UUID, vector: Sequence[float], limit: int) -> list[VectorHit]:
        with _translate_errors():
            response = self._client.query_points(
                self._collection,
                query=list(vector),
                query_filter=_match("owner_id", owner_id),
                limit=limit,
                with_payload=True,
            )
        return [_to_hit(point.score, point.payload or {}) for point in response.points]

    def _delete(self, selection: models.Filter) -> None:
        self._client.delete(
            self._collection, points_selector=models.FilterSelector(filter=selection), wait=True
        )

    def _check_dimension(self) -> None:
        vectors = self._client.get_collection(self._collection).config.params.vectors
        size = vectors.size if isinstance(vectors, models.VectorParams) else None
        if size != self._dimension:
            raise ValueError(
                f"Qdrant koleksiyonu {size} boyutlu ama EMBEDDING_DIM={self._dimension}. "
                "Koleksiyonu silip indeksi yeniden üretin "
                '(docs/adr/ADR-005, "Kurtarma").'
            )


class QdrantProbe:
    """`/health/ready` için Qdrant'a ulaşılıp ulaşılamadığını kontrol eder."""

    def __init__(self, client: QdrantClient) -> None:
        self._client = client

    @property
    def name(self) -> str:
        return "qdrant"

    def is_ready(self) -> bool:
        try:
            self._client.get_collections()
        except QDRANT_ERRORS as error:
            logger.warning("qdrant_unreachable", error_type=type(error).__name__)
            return False
        return True


def _match(field: str, value: UUID, *, chunk_no_from: int | None = None) -> models.Filter:
    conditions = [models.FieldCondition(key=field, match=models.MatchValue(value=str(value)))]
    if chunk_no_from is not None:
        conditions.append(
            models.FieldCondition(key="chunk_no", range=models.Range(gte=chunk_no_from))
        )
    return models.Filter(must=conditions)


@contextmanager
def _translate_errors() -> Iterator[None]:
    """Geçici Qdrant hatalarını 503'e çevirir; kalıcı hataları olduğu gibi bırakır.

    Bağlantı/zaman aşımı, 429 ve 5xx geçicidir: yeniden denemek işe yarayabilir. 404 (koleksiyon
    yok) veya 400 (yanlış vektör boyutu) gibi hatalar yanlış ayar veya programlama hatasıdır;
    bunları "servis şu an yok" diye göstermek, boşuna ve ücretli yeniden denemelere yol açar.
    """
    try:
        yield
    except QDRANT_ERRORS as error:
        if not _is_transient(error):
            raise
        raise _unavailable(error) from error


def _is_transient(error: Exception) -> bool:
    if isinstance(error, UnexpectedResponse) and error.status_code is not None:
        return error.status_code == TOO_MANY_REQUESTS or error.status_code >= SERVER_ERROR
    return True


def _to_hit(score: float, payload: dict[str, Any]) -> VectorHit:
    return VectorHit(
        page_id=UUID(str(payload["page_id"])),
        chunk_no=int(payload["chunk_no"]),
        score=score,
        text=str(payload["text"]),
        heading_path=str(payload["heading_path"]),
        page_title=str(payload["page_title"]),
    )


def _unavailable(error: Exception) -> ExternalServiceError:
    logger.warning("qdrant_error", error_type=type(error).__name__)
    return ExternalServiceError(
        "Arama servisine şu an ulaşılamıyor.", code=VECTOR_STORE_UNAVAILABLE
    )
