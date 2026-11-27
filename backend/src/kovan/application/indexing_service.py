"""Arka plan indeksleme servisi (ADR-005, R-10, R-11).

Bir tur: Düzenlemesi bitmiş (settle süresi geçmiş) ve indekslenmeyi bekleyen sayfaları al →
silinmişse vektörlerini sil, değilse parçala → embedding'e çevir → Qdrant'a yaz → sayfayı
"indekslendi" işaretle. Hata olursa sayfa artan beklemeyle yeniden denenmek üzere işaretlenir.

Sayfa tablosu ve parçalama fonksiyonu servise yalnızca `PendingPages` ve `Chunker`
arayüzleriyle bağlanır (`application/ports/indexing.py`); böylece servis onlardan bağımsız
olarak test edilebilir.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from kovan.application.errors import ExternalServiceError
from kovan.application.ports.ai import EmbeddingProvider
from kovan.application.ports.indexing import Chunker, PageToIndex, PendingPages
from kovan.application.ports.vector import VectorIndex, VectorPoint

BASE_RETRY_SECONDS = 5
UNEXPECTED_ERROR_CODE = "INDEXING_FAILED"


@dataclass(frozen=True)
class IndexRunReport:
    indexed: int = 0
    removed: int = 0
    failed: int = 0
    # Dış servis hatası dışındaki hatalar (ör. yanlış ayar). Uygulama katmanı log yazamadığı için
    # hatalar burada döngüye taşınır ve orada ayrıntısıyla loglanır; hiçbiri yutulmaz.
    unexpected_errors: tuple[Exception, ...] = field(default=())

    @property
    def did_work(self) -> bool:
        return self.indexed + self.removed + self.failed > 0


class IndexingService:
    def __init__(
        self,
        pending_pages: PendingPages,
        chunker: Chunker,
        embeddings: EmbeddingProvider,
        vector_index: VectorIndex,
        *,
        settle_seconds: int = 10,
        batch_size: int = 10,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._pending_pages = pending_pages
        self._chunker = chunker
        self._embeddings = embeddings
        self._vector_index = vector_index
        self._settle = timedelta(seconds=settle_seconds)
        self._batch_size = batch_size
        self._clock = clock

    def run_once(self, now: datetime) -> IndexRunReport:
        """Bekleyen sayfalardan bir grubu işler; arka plan döngüsü birkaç saniyede bir çağırır.

        Bir sayfadaki hata diğer sayfaları durdurmaz. Hatalı sayfa yeniden denenmek üzere
        işaretlenir; böylece deneme sınırı (R-11) işler ve sayfa sonsuza kadar denenmez.
        Beklenmeyen hatalar (ör. yanlış ayar) raporla döngüye iletilir ve orada loglanır.
        """
        indexed = removed = failed = 0
        unexpected: list[Exception] = []
        pages = self._pending_pages.pages_to_index(
            settled_before=now - self._settle, limit=self._batch_size
        )
        for page in pages:
            try:
                self._process(page)
            except ExternalServiceError as error:
                self._mark_failed(page, error.code)
                failed += 1
            except Exception as error:
                self._mark_failed(page, UNEXPECTED_ERROR_CODE)
                failed += 1
                unexpected.append(error)
            else:
                self._pending_pages.mark_indexed(page_id=page.page_id, version=page.version)
                if page.deleted:
                    removed += 1
                else:
                    indexed += 1
        return IndexRunReport(indexed, removed, failed, unexpected_errors=tuple(unexpected))

    def _process(self, page: PageToIndex) -> None:
        if page.deleted:
            self._vector_index.delete_page(page_id=page.page_id)
        else:
            self._index(page)

    def _index(self, page: PageToIndex) -> None:
        chunks = list(self._chunker(page.title, page.content))
        # ADR-009: Embedding'e giden metnin başına bağlam başlığı eklenir.
        vectors = self._embeddings.embed([f"{c.heading_path}\n\n{c.text}" for c in chunks])
        points = [
            VectorPoint(chunk_no=i, vector=vector, text=chunk.text, heading_path=chunk.heading_path)
            for i, (chunk, vector) in enumerate(zip(chunks, vectors, strict=True))
        ]
        # Boş sayfada `points` boştur; replace_page yine de eski parçaları temizler.
        self._vector_index.replace_page(
            owner_id=page.owner_id,
            page_id=page.page_id,
            page_title=page.title,
            page_version=page.version,
            points=points,
        )

    def _mark_failed(self, page: PageToIndex, error_code: str) -> None:
        # R-11: Bekleme 5 × 2^n sn; n = o ana kadarki başarısız deneme sayısı (5, 10, 20, 40).
        # Süre hatanın olduğu andan sayılır: Uzun bir zaman aşımından sonra turun başlangıç
        # zamanı kullanılsaydı yeniden deneme anı çoktan geçmiş olurdu.
        retry_at = self._clock() + timedelta(seconds=BASE_RETRY_SECONDS * 2**page.attempts)
        self._pending_pages.mark_failed(
            page_id=page.page_id, version=page.version, error_code=error_code, retry_at=retry_at
        )
