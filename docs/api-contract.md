# REST API Sözleşmesi

> Frontend ve backend'in paralel geliştirilebilmesi için ortak sözleşme. Kod yazılınca FastAPI'nin ürettiği OpenAPI (`/docs`) asıl kaynak olur; bu doküman onunla tutarlı tutulur.

## Genel kurallar

- Temel yol: **`/api/v1`**
- Gövdeler **JSON**, alan adları `snake_case`.
- Kimlik doğrulama: `kovan_session` çerezi (`HttpOnly; SameSite=Strict; Path=/api`, prod'da `Secure`). Aksi belirtilmedikçe tüm uç noktalar oturum ister; yoksa **401**.
- RESTful: oluşturma `POST`, tam güncelleme `PUT`, kısmi işlem `PATCH`, silme `DELETE` (hocanın lesson01 API standardı).
- Listeleme uç noktaları **sayfalıdır**: `?limit=20&offset=0` (limit ≤ 100). Yanıt: `{ "items": [...], "total": 57, "limit": 20, "offset": 0 }`.
- Başka kullanıcının kaynağı **404** döner (403 değil).
- Her yanıtta `X-Request-ID` başlığı vardır.

### Hata formatı

```json
{
  "error": {
    "code": "PAGE_MOVE_CYCLE",
    "message": "Bir sayfa kendi alt sayfasının altına taşınamaz.",
    "rule": "R-05",
    "request_id": "8f2c1a7e-..."
  }
}
```

| HTTP | `code` örnekleri |
| --- | --- |
| 401 | `UNAUTHENTICATED`, `INVALID_CREDENTIALS` |
| 404 | `PAGE_NOT_FOUND`, `SESSION_NOT_FOUND` |
| 409 | `EMAIL_TAKEN`, `VERSION_CONFLICT` |
| 422 | `VALIDATION_ERROR`, `CONTENT_INVALID`, `PAGE_MOVE_CYCLE` |
| 429 | `TOO_MANY_ATTEMPTS` |
| 503 | `AI_SERVICE_UNAVAILABLE`, `VECTOR_STORE_UNAVAILABLE` |
| 500 | `INTERNAL_ERROR` (detay yok) |

---

## Kimlik — `/auth` 🟥

| Metot | Yol | Gövde | Başarılı | Hatalar | Hikaye |
| --- | --- | --- | --- | --- | --- |
| POST | `/auth/register` | `{email, password, display_name}` | **201** `User` | 409, 422 | US-01 |
| POST | `/auth/login` | `{email, password}` | **204** + `Set-Cookie` | 401, 429 | US-02 |
| POST | `/auth/logout` | — | **204** (çerez silinir) | — | US-02 |
| GET | `/auth/me` | — | **200** `User` | 401 | US-02 |

`User` = `{id, email, display_name, created_at}`; `password_hash` asla yok.

## Sayfalar — `/pages`

| Metot | Yol | Gövde / Sorgu | Başarılı | Hatalar | Öncelik / Hikaye |
| --- | --- | --- | --- | --- | --- |
| GET | `/pages/tree` | — | **200** `TreeNode[]` (silinmemiş sayfalar, en fazla 1000) | — | 🟥 US-05 |
| POST | `/pages` | `{title?, parent_id?, content?}` | **201** `Page` | 404 (parent), 422 | 🟥 US-03, US-05 |
| GET | `/pages/{id}` | — | **200** `Page` | 404 | 🟥 US-03 |
| PUT | `/pages/{id}` | `{title, content, version}` | **200** `Page` | 404, 409, 422 | 🟥 US-04 |
| DELETE | `/pages/{id}` | — | **204** (sayfa + alt sayfalar silindi işaretlenir) | 404 | 🟥 US-06 |
| GET | `/pages/{id}/backlinks` | — | **200** `PageSummary[]` | 404 | 🟥 US-08 |
| GET | `/pages/titles` | `ids=uuid,uuid,…` (≤ 100) | **200** `{id, title, deleted}[]` (bağlantı gösterimi için) | — | 🟥 US-07 |
| PATCH | `/pages/{id}/move` | `{parent_id: uuid \| null}` | **200** `Page` | 404, 422 | 🟧 US-05 |
| GET | `/pages/recent` | `limit, offset` | **200** sayfalı `PageSummary` | — | 🟧 US-14 |
| GET | `/trash` | `limit, offset` | **200** sayfalı `PageSummary` | — | 🟧 US-06 |
| POST | `/trash/{id}/restore` | — | **200** `Page` | 404 | 🟧 US-06 |
| DELETE | `/trash/{id}` | — | **204** (kalıcı silme) | 404 | 🟧 US-06 |

```jsonc
// Page
{
  "id": "9a2e…", "parent_id": null, "title": "Veritabanı",
  "content": [ { "type": "heading", "props": { "level": 2 }, "content": [ { "type": "text", "text": "Normalizasyon", "styles": {} } ] } ],
  "version": 7,
  "index_status": "INDEXED",            // INDEXED | PENDING | FAILED
  "breadcrumbs": [ { "id": "11aa…", "title": "Dersler" } ],
  "created_at": "…", "updated_at": "…"
}
// TreeNode (kardeşler başlığa göre alfabetik)
{ "id": "…", "parent_id": "…", "title": "…", "has_children": true }
// PageSummary
{ "id": "…", "title": "…", "breadcrumbs": [ … ], "updated_at": "…" }
```

> `/pages/titles`: Editördeki `@` bağlantılarının güncel başlığını ve silinmiş olup olmadığını göstermek için (AC-07.3). Kullanıcıya ait olmayan kimlikler `deleted: true` gibi davranır, bilgi sızdırılmaz.

## Arama — `/search` 🟥

| Metot | Yol | Sorgu | Başarılı | Hatalar | Hikaye |
| --- | --- | --- | --- | --- | --- |
| GET | `/search` | `q` (1–200 karakter), `mode=keyword\|semantic`, `limit`, `offset` | **200** sayfalı `SearchResult` | 422, 503 (semantic) | US-09, US-10 |

```jsonc
// SearchResult
{ "page_id": "…", "title": "Veritabanı", "heading_path": "Veritabanı › Normalizasyon",
  "snippet": "… normalizasyon kuralları …",   // düz metin; vurgulamayı frontend yapar
  "score": 0.82 }
```

## Sohbet — `/chat`

| Metot | Yol | Gövde | Başarılı | Hatalar | Öncelik / Hikaye |
| --- | --- | --- | --- | --- | --- |
| POST | `/chat` | `{question (1–1000 karakter)}` · Should: `session_id?` | **200** `ChatAnswer` | 404 (session), 422, 503 | 🟥 US-11 |
| GET | `/chat/sessions` | `limit, offset` | **200** sayfalı `{id, title, created_at}` | — | 🟧 US-13 |
| GET | `/chat/sessions/{id}` | — | **200** `{id, title, messages: ChatMessage[]}` | 404 | 🟧 US-13 |

```jsonc
// ChatAnswer
{
  "answer": "3NF'de geçişli bağımlılık kaldırılır [1]; BCNF ise her belirleyicinin aday anahtar olmasını ister [1].",
  "citations": [ { "index": 1, "page_id": "…", "page_title": "Veritabanı", "heading_path": "Veritabanı › Normalizasyon" } ],
  "found": true,          // false → "bulamadım" cevabı, citations boş
  "session_id": null      // Should: sohbet geçmişi açıkken dolu
}
```

## Sağlık

| Metot | Yol | Açıklama |
| --- | --- | --- |
| GET | `/health` | Canlılık (oturum gerekmez) |
| GET | `/health/ready` | PostgreSQL + Qdrant erişimi (oturum gerekmez) |

## Yönetim (CLI, HTTP değil)

```bash
uv run python -m kovan.cli reindex --all          # Qdrant'ı PostgreSQL'den baştan üret
uv run python -m kovan.cli reindex --page <id>
uv run python -m kovan.cli token-report           # Should: token kullanımı ve tahmini maliyet
```
