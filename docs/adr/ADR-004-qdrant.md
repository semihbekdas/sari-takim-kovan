# ADR-004: Vektör Veritabanı — Qdrant

## Durum

Kabul Edildi *(Accepted)* — 2026-11-13

## Bağlam

- Anlamsal arama ve RAG için sayfa parçalarının embedding vektörlerini saklayıp **kosinüs benzerliği** ile sorgulamamız gerekiyor (ders Bölüm 9).
- Ders rehberi P0007 için "Qdrant/Vektör Veritabanı" öneriyor; derste Qdrant kullanıldı (ders reposunun kökündeki `docker-compose.yml`). Projede de PostgreSQL ile birlikte kendi `docker-compose.yml`'mizle çalıştırılır *(planlanan)*.
- Çok kullanıcılı sistemde her arama **kullanıcıya göre filtrelenmeli** (güvenlik, R-12).

## Karar

Vektörler **Qdrant**'ta tutulur:
- Tek koleksiyon: `page_chunks`, mesafe **Cosine**, boyut `EMBEDDING_DIM`.
- Payload: `owner_id`, `page_id`, `page_title`, `heading_path`, `chunk_no`, `text`, `page_version`; `owner_id` ve `page_id` için **payload indeksi**.
- Nokta kimliği deterministik: `uuid5(page_id:chunk_no)` (idempotent upsert, ADR-005).
- Qdrant'a erişim yalnızca `VectorIndex` portu üzerinden; portun `search` metodu **`owner_id` parametresi olmadan çağrılamaz**.
- Qdrant **türetilmiş veridir**: Kaynak PostgreSQL'dir; `reindex` komutu ile baştan üretilebilir.

## Değerlendirilen alternatifler

| Alternatif | Artısı | Neden seçilmedi |
| --- | --- | --- |
| **pgvector** (PostgreSQL eklentisi) | Tek veritabanı, transaction içinde tutarlılık, daha az servis | Ders içeriği ve önerisiyle uyumu düşük; Qdrant'ın filtreli arama ve dashboard özellikleri sunumda vektör veritabanı bilgisini göstermeye daha uygun. Tutarlılık sorununu sürüm işaretli indekslemeyle çözüyoruz (ADR-005). **Süre çok sıkışırsa yedek plan:** `VectorIndex` portunun pgvector adaptörüyle değiştirilmesi (yalnızca infrastructure etkilenir). |
| **Chroma / FAISS** | Hafif, kolay | FAISS bir kütüphane, sunucu değil (filtreleme ve kalıcılık bizde kalır); Chroma ile ders örnekleri yok. |
| **Elasticsearch** (kNN + full-text) | Hibrit arama tek yerde | Kaynak tüketimi yüksek, kurulumu ağır (ders Bölüm 4'te Loki ile karşılaştırması yapılmıştı). |

## Sonuçlar

**Avantajlar:**
- Dersle birebir uyumlu; `http://localhost:6333/dashboard` ile koleksiyon sunumda gösterilebilir.
- Payload filtreleri ile kullanıcı izolasyonu sorgu seviyesinde sağlanır.
- Docker ile tek satırda ayağa kalkar, Testcontainers ile test edilir.

**Değiş tokuşlar:**
- İki ayrı veri deposu → **tutarlılık sorunu** (sayfa silinip vektörü kalabilir). Çözüm: ADR-005 (sürüm işaretli indeksleme + aramada PostgreSQL doğrulaması + `reindex`).
- Embedding modeli değişirse koleksiyon boyutu değişir → tam yeniden indeksleme gerekir.
