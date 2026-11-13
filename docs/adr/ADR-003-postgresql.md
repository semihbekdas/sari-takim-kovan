# ADR-003: Ana Veritabanı — PostgreSQL (İçerik JSONB), SQLAlchemy Core + Alembic

## Durum

Kabul Edildi *(Accepted)* — 2026-11-13

## Bağlam

- Ders şartı: en az bir veritabanı.
- Veri hem **ilişkisel** (kullanıcı → sayfa, sayfa hiyerarşisi, sayfa → sayfa bağlantıları) hem de **belge benzeri** (BlockNote blok dizisi).
- Sayfa kaydı ve bağlantıların yeniden yazılması **tek transaction**'da olmalı; indeksleme durumu da aynı satırda tutulacak (ADR-005).
- Kelime araması gerekiyor (F-18).
- Hocanın lesson05 örneğinde EF Core yerine **Dapper** (mikro-ORM) seçilmişti; gerekçe SQL üzerinde kontrol ve sadelikti.

## Karar

- Ana veritabanı **PostgreSQL**.
- Sayfa içeriği tek bir **`jsonb`** kolonunda (BlockNote blok dizisi) saklanır; blok başına satır tutulmaz. Arama ve parçalama için içerikten türetilen `plain_text` kolonu da saklanır.
- Kelime araması PostgreSQL **full-text search** ile (`tsvector` + GIN indeks, `simple` sözlük).
- Hiyerarşi `parent_id` ile; alt ağaç ve breadcrumb sorguları **recursive CTE** ile.
- Veri erişimi **SQLAlchemy 2.x Core** ile: tablo tanımları + açık `select`/`insert`/`update` ifadeleri, repository'lerde domain nesnelerine elle eşleme. **ORM (Session, lazy loading) kullanılmaz.** Şema değişiklikleri **Alembic** migration'larıyla.
- Birincil anahtarlar **UUID** (uygulama tarafında üretilir).

## Değerlendirilen alternatifler

| Alternatif | Neden seçilmedi |
| --- | --- |
| **MongoDB** | Blok içeriği için doğal ama hiyerarşi, bağlantılar ve tutarlı güncellemeler PostgreSQL'de daha kolay; PostgreSQL JSONB ikisini birden karşılıyor. |
| **Blok başına satır** (Notion'ın kendi modeli) | Sıralama, iç içe bloklar ve kısmi güncelleme çok karmaşık; BlockNote tüm dokümanı tek JSON olarak veriyor; ortak düzenleme yapmıyoruz. |
| **SQLite** | Kurulumu en kolay ama eşzamanlı yazma ve full-text arama yetenekleri sınırlı; Testcontainers ile PostgreSQL zaten kolay. |
| **SQLAlchemy ORM / SQLModel** | Daha az SQL yazdırır ama Session yaşam döngüsü, lazy loading ve ORM modeli ↔ domain nesnesi ikiliği yeni başlayanlar ve ajanlar için hata kaynağı. Core, hocanın Dapper tercihine en yakın Python karşılığı. |
| **Ham SQL (psycopg)** | Mümkün ama Alembic ile şema tanımı ve tip güvenliği için Core daha iyi; Core gerektiğinde ham SQL'e de izin veriyor. |

## Sonuçlar

**Avantajlar:**
- Tek veritabanında hem ilişkisel bütünlük (FK, unique) hem esnek içerik.
- Sayfa + bağlantılar + indeks durumu atomik yazılır (tutarlılığın temeli).
- SQL açık ve okunabilir; sunumda "bu sorgu ne yapıyor?" sorusuna doğrudan cevap verilebilir.
- Testcontainers ile gerçek PostgreSQL üzerinde entegrasyon testi.

**Değiş tokuşlar:**
- Repository'lerde satır ↔ domain nesnesi eşleme kodu elle yazılır.
- JSONB içindeki tek bir bloğu sorgulamak zordur (ihtiyacımız yok).
- `simple` sözlük Türkçe kök bulma yapmaz ("kitaplar" ≠ "kitap"); bu açığı anlamsal arama kapatır.
