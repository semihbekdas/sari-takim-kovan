# REST API Sözleşmesi

> Frontend ve backend'in paralel geliştirilebilmesi için ortak sözleşme. Kod yazılınca FastAPI'nin ürettiği OpenAPI (Swagger arayüzü: `/api/docs`) asıl kaynak olur; bu doküman onunla tutarlı tutulur.

## Genel kurallar

- Temel yol: **`/api/v1`**
- Gövdeler **JSON**, alan adları `snake_case`. İstisna: `content` içindeki BlockNote blokları kendi biçiminde (camelCase alanlarla) olduğu gibi saklanır.
- Kimlik doğrulama: `kovan_session` çerezi (`HttpOnly; SameSite=Strict; Path=/api`, prod'da `Secure`). Aksi belirtilmedikçe tüm uç noktalar oturum ister; yoksa **401**.
- RESTful: oluşturma `POST`, tam güncelleme `PUT`, kısmi işlem `PATCH`, silme `DELETE` (hocanın lesson01 API standardı).
- Listeleme uç noktaları **sayfalıdır**: `?limit=20&offset=0` (limit ≤ 100). Yanıt: `{ "items": [...], "total": 57, "limit": 20, "offset": 0 }`. İstisna: Boyutu üst sınırlı olan ağaç (≤ 1000) ve *(Should)* geri bağlantılar (≤ 100) düz liste döner (`/pages/tree`, `/pages/{id}/backlinks`).
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

- `rule` yalnızca bir domain kuralı (R-xx) ihlalinde doludur, aksi halde `null`.
- `VALIDATION_ERROR` yanıtında ek olarak hangi alanın hatalı olduğunu söyleyen `details` listesi bulunur: `[{"field": "body.email", "message": "Bu alan zorunludur."}]`. Mesajlar Türkçedir; girilen değer (ör. şifre) yanıta konmaz.
- **Doğrulama nerede?** API şeması tipleri, zorunlu alanları ve taşıma sınırlarını (ör. arama sorgusu 1–200, soru 1–1000 karakter, `limit` ≤ 100) denetler (`VALIDATION_ERROR`). Kural kodlu sınırlar (R-01 e-posta biçimi, R-02 şifre uzunluğu, R-03 başlık, R-06 içerik) şemada tekrarlanmaz; domain'de kontrol edilir ve `rule` alanıyla döner. Bu yanıtlarda `message` hatalı alanı adıyla söyler (ör. "Şifre en az 8 karakter olmalı.").
- Beklenmeyen hatalarda (500) iç ayrıntı istemciye gönderilmez; `request_id` ile loglarda aranır.

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
| GET | `/pages/{id}/backlinks` | — | **200** `PageSummary[]` (en fazla 100, en son düzenlenen önce) | 404 | 🟧 US-08 |
| PATCH | `/pages/{id}/move` | `{parent_id: uuid \| null}` | **200** `Page` | 404, 422 | 🟧 US-05 |
| GET | `/pages/recent` | `limit, offset` | **200** sayfalı `PageSummary` | — | 🟧 US-14 |
| GET | `/trash` | `limit, offset` | **200** sayfalı `PageSummary` | — | 🟧 US-06 |
| POST | `/trash/{id}/restore` | — | **200** `Page` | 404 | 🟧 US-06 |
| DELETE | `/trash/{id}` | — | **204** (kalıcı silme; önce Qdrant noktaları silinir, ADR-005) | 404, 503 (Qdrant'a ulaşılamazsa satır silinmez) | 🟧 US-06 |

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

> Sabit yollar (`/pages/tree`, `/pages/recent`) router'da `/pages/{id}`'den **önce** tanımlanır; aksi halde FastAPI bunları sayfa kimliği sanıp 422 döner.

> **`@` bağlantıları için ayrı bir uç nokta yoktur.** Bağlantının güncel başlığı ve `@` menüsündeki sayfa listesi, frontend'de zaten yüklü olan `/pages/tree` yanıtından bulunur. Ağaçta olmayan bir sayfa kimliği (silinmiş ya da başka kullanıcıya ait) "silinmiş sayfa" olarak gösterilir (AC-07.3); böylece başka kullanıcının sayfası hakkında bilgi sızmaz. **Bilinen sınır:** Ağaç en fazla 1000 sayfa döndürür; 1000'den fazla sayfası olan bir kullanıcıda ağacın dışında kalan sayfalara verilen bağlantılar da "silinmiş" görünür. Ders projesi ölçeğinde bu sınır kabul edildi; gerekirse kimliğe göre başlık soran bir uç nokta eklenir.

## Arama — `/search` 🟥

| Metot | Yol | Sorgu | Başarılı | Hatalar | Hikaye |
| --- | --- | --- | --- | --- | --- |
| GET | `/search` | `q` (1–200 karakter), `limit`, `offset` · Should: `mode=semantic\|keyword` (varsayılan `semantic`) | **200** sayfalı `SearchResult` | 422, 503 | US-10 · 🟧 US-09 |

```jsonc
// SearchResult
{ "page_id": "…", "title": "Veritabanı", "heading_path": "Veritabanı › Normalizasyon",
  "snippet": "… normalizasyon kuralları …",   // düz metin; vurgulamayı frontend yapar
  "score": 0.82 }
```

- Arama **anlamsaldır**: En fazla 20 sonuç döner (`total` ≤ 20); `score` kosinüs benzerliğidir.
- *(Should)* `mode=keyword`: `heading_path` boştur (`null`) ve `score` PostgreSQL tam metin sıralama puanıdır.

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
  "found": true,          // true → cevap en az bir geçerli kaynağa dayanıyor
                          // false → answer sabit bir bilgi mesajıdır ("bulamadım" veya "üretilemedi"), citations boş
  "session_id": null      // Should: sohbet geçmişi açıkken dolu
}
```

## Sağlık

| Metot | Yol | Açıklama |
| --- | --- | --- |
| GET | `/health` | Canlılık (oturum gerekmez) |
| GET | `/health/ready` | PostgreSQL + Qdrant erişimi; biri erişilemezse **503** (oturum gerekmez) |

## Yönetim (CLI, HTTP değil) *(Should)*

```bash
uv run python -m kovan.cli token-report           # Should: token kullanımı ve tahmini maliyet
```

> Ayrı bir `reindex` komutu yoktur. Qdrant türetilmiş veridir; indeksin baştan üretilmesi iki adımdır: [ADR-005](adr/ADR-005-surum-isaretli-indeksleme.md), "Kurtarma".
