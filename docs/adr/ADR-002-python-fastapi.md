# ADR-002: Backend Dili ve Çatısı — Python + FastAPI

## Durum

Kabul Edildi *(Accepted)* — 2026-11-13

## Bağlam

- Ders rehberi P0007 için **"Python (FastAPI) veya .NET backend + Qdrant"** öneriyor.
- Projenin kalbi RAG; derste RAG örnekleri (lesson07/08) Python + `qdrant-client` + `openai` istemcisi ile yazıldı.
- Ekipte iki üye elektronik bölümünden; Python, C#'a göre bu üyeler için daha tanıdık ve okunması kolay.
- Sunumda herkesin koda hakim olması gerekiyor.

## Karar

Backend **Python 3.12** ve **FastAPI** ile yazılır. Destekleyici kütüphaneler: Pydantic v2 (yalnızca `api` katmanında şema/doğrulama), `pydantic-settings` (yapılandırma), SQLAlchemy 2.x **Core** + Alembic (ADR-003), `qdrant-client` (ADR-004), resmi `anthropic` ve `openai` SDK'ları (ADR-006), structlog (JSON log). Bağımlılık ve sanal ortam yönetimi **uv** ile yapılır (kilit dosyası commit'lenir).

## Değerlendirilen alternatifler

| Alternatif | Neden seçilmedi |
| --- | --- |
| **.NET 10 + ASP.NET Core** | Hocanın örneklerinin çoğu .NET; mimari örnekler güçlü. Ancak RAG ekosistemi ve ekibin aşinalığı Python'da daha iyi; iki dil (C# + TS) yerine Python + TS öğrenme yükü daha az. |
| **Node.js (Express/Nest)** | Frontend ile aynı dil avantajı var ama RAG/embedding araçları ve ders örnekleri Python'da. |
| **Django** | Yerleşik ORM ve admin güçlü ama "batteries included" yapı, katman ayrımımızı (ADR-001) zorlaştırır; API odaklı projede FastAPI daha hafif. |

## Sonuçlar

**Avantajlar:**
- Ders RAG örnekleri doğrudan referans alınabilir.
- FastAPI otomatik OpenAPI/Swagger üretir → API sözleşmesi (`api-contract.md`) ile kod tutarlılığı kolay doğrulanır.
- Pydantic ile istek doğrulama ve 422 hataları standart gelir.
- SonarQube Cloud Python'u destekler; ruff + mypy ile güçlü statik analiz.

**Değiş tokuşlar:**
- Dinamik tipli dil: Tip hataları ancak mypy ile yakalanır → mypy CI'da zorunlu.
- Async/sync karışımı dikkat ister. Karar: Veritabanı erişimi senkron SQLAlchemy Core (FastAPI senkron uç noktaları thread havuzunda çalıştırır); indeksleme döngüsü ayrı bir arka plan görevidir ve senkron çağrıları thread'de yürütür.
