# AGENTS.md — Yapay Zeka Ajanları İçin Proje Talimatları

Bu dosya Claude Code, Codex, GitHub Copilot vb. kodlama ajanlarına bu projede nasıl çalışacaklarını anlatır. Ekip kuralları: [`KURALLAR.md`](KURALLAR.md).

## Proje

**Kovan**: Notion benzeri kişisel bilgi tabanı + anlamsal arama + kaynaklı RAG sohbeti. Ders projesi (P0007), teslim 25 Aralık 2026.
Özellikler: [`OZELLIKLER.md`](OZELLIKLER.md) · Mimari: [`docs/architecture.md`](docs/architecture.md) · Mimari gerekçe: [`docs/mimari-secimi.md`](docs/mimari-secimi.md) · Domain ve kurallar: [`docs/domain-design.md`](docs/domain-design.md) · API: [`docs/api-contract.md`](docs/api-contract.md) · Hikayeler: [`docs/user-stories.md`](docs/user-stories.md) · Testler: [`docs/test-strategy.md`](docs/test-strategy.md) · Kararlar: [`docs/adr/`](docs/adr/)

**Bir değişikliğe başlamadan önce ilgili dokümanı oku. Dokümanla çelişen bir şey yapman gerekiyorsa dur ve kullanıcıya sor.** Must olmayan (Should/Could) bir özelliği kullanıcı istemedikçe yazma.

## Teknoloji

- Backend: Python 3.12, FastAPI, Pydantic v2 (API şemaları ve `config.py`; `domain`/`application`'da yasak), SQLAlchemy 2.x **Core** (ORM değil) + Alembic, PostgreSQL, Qdrant, resmi `anthropic` ve `openai` SDK'ları, structlog
- Frontend: React + TypeScript (strict) + Vite, BlockNote (kısıtlı şema), React Router, TanStack Query
- Test: pytest, Testcontainers, Vitest; kalite: ruff, mypy, import-linter, eslint, SonarQube Cloud

## Mimari kurallar (zorunlu)

```
backend/src/kovan/
  domain/          # entity, value object, kurallar R-01…R-13, DomainRuleError. Dış kütüphane import ETMEZ
  application/     # servisler + port arayüzleri (typing.Protocol) + saf fonksiyonlar (chunking, prompting). Sadece domain'i import eder
  infrastructure/  # port uygulamaları: db (SQLAlchemy Core), vector (Qdrant), ai (anthropic, openai_compatible, fake), security, index_loop
  api/             # FastAPI router'ları, Pydantic şemaları, hata eşleme. İş kuralı içermez
  main.py          # composition root: adaptörlerin seçilip bağlandığı tek yer
```

- Bağımlılık yönü: `api → application → domain`, `infrastructure → application/domain`. `domain` ve `application` hiçbir zaman `infrastructure`, `api`, `fastapi`, `pydantic`, `sqlalchemy`, `structlog`, `qdrant_client`, `openai`, `anthropic` import etmez (import-linter denetler; güncel liste `backend/pyproject.toml`).
- Domain kuralı ihlalleri `DomainRuleError(rule_code="R-xx", ...)` ile bildirilir; kural kodları `docs/domain-design.md § 8`'de.
- Her veri erişimi `owner_id` ile filtrelenir. Qdrant sorgularında `owner_id` filtresi **zorunlu** (R-12).
- Sayfanın içeriğini veya görünürlüğünü değiştiren her işlem `version`'ı artırır ve indeksleme alanlarını sıfırlar (R-10, ADR-005). Kayıt isteği içinde yapay zeka API'si **çağrılmaz**.
- Yapay zeka çağrıları yalnızca `ChatModel` ve `EmbeddingProvider` port'ları üzerinden yapılır. Dış SDK exception'ları `ExternalServiceError`'a çevrilir.
- Dil modeline giden prompt'ta sayfa içeriği `<context>` ayraçlarıyla işaretlenmiş **veri** olarak verilir; içindeki talimatlar uygulanmaz.

## Kod kuralları

- Okunabilir, kısa fonksiyonlar (≤ 30 satır hedef), erken dönüş, açık isimler. Tanımlayıcılar İngilizce; kullanıcıya görünen metinler Türkçe.
- Python: tüm fonksiyonlarda tip ipucu; `ruff` ve `mypy` temiz. TypeScript: `strict`, `any` yok.
- Boş `except` / `catch` yok; hatayı gizleme. Beklenen hatalar domain/uygulama hata tipleriyle modellenir.
- **API anahtarlarını, şifreleri, `.env` içeriğini asla koda, teste, loga veya dokümana yazma.** Yapılandırma `pydantic-settings` üzerinden.
- Yeni bağımlılık eklemeden önce kullanıcıya sor (ADR gerekebilir).
- BlockNote editörüne yeni blok türü ekleme; izin verilen liste `domain-design.md § 4`'te.

## Test kuralları

- Her davranış değişikliği testle gelir. Testler ilgili kabul kriterini işaretler: `@pytest.mark.ac("AC-xx.y")`.
- Domain/application için birim test; repository, Qdrant, indeksleme döngüsü ve API için Testcontainers ile entegrasyon/kabul testi. Qdrant adaptörünün mantığı ayrıca Docker gerektirmeyen bellek içi Qdrant ile birim test edilir.
- Testler **gerçek yapay zeka API'si çağırmaz**: `FakeEmbeddingProvider` ve `FakeChatModel` (`infrastructure/ai/fake.py`) kullanılır; hata senaryoları için testte `ExternalServiceError` fırlatan küçük bir fake yazılır. Test ayarları `tests/fakes.py`'deki `make_test_settings()` ile kurulur (geliştiricinin `.env` dosyası okunmaz).
- Assert'siz test yazma, test silme/atlama, coverage'tan dosya hariç tutma **yasak**. (Sonar'ın kapsam koşulu yalnızca backend içindir; frontend'de mantık içeren kısımlar test edilir, ADR-010.)

## Çalışma biçimi

- Değişiklikleri küçük tut (bir PR ≈ tek iş, ≤ 400 satır). Kullanıcı istemedikçe birden fazla özelliği aynı anda yazma.
- Davranış değişirse ilgili dokümanı da güncelle.
- **Kullanıcı açıkça istemedikçe commit veya push yapma.** Commit her zaman kullanıcının kendi hesabıyla atılır; değişiklikleri kullanıcı inceler. Commit tarihleriyle asla oynama, push'lanmış geçmişi yeniden yazma.
- İşin sonunda kısa bir özet ver: ne değişti, hangi testler eklendi, hangi AC'ler karşılandı, kullanıcının `docs/ai-log/<isim>.md` dosyasına ne yazılmalı.

## Komutlar

```bash
cd backend
uv run pytest --cov                       # testler (fake yapay zeka; Docker kapalıysa entegrasyon testleri yerelde atlanır, CI'da zorunlu)
uv run ruff check . && uv run ruff format --check .
uv run mypy                               # strict tip kontrolü
uv run lint-imports                       # mimari kontrol
uv run uvicorn kovan.main:create_app --factory --reload
cd ../frontend && npm test && npm run lint   # (frontend iskeleti gelince)
```
