# ADR-001: Katmanlı Mimari + Port/Adapter, Modüler Monolit

## Durum

Kabul Edildi *(Accepted)* — 2026-11-13

## Bağlam

- 3 kişilik ekip, ~4 haftalık geliştirme süresi (kod dondurma 13 Aralık), ders projesi ölçeğinde trafik.
- Ders kriterleri: **mimari uyum**, **test edilebilirlik**, **okunabilirlik**, **teknik borç (Sonar A)**.
- Kodun büyük kısmı yapay zeka ajanlarıyla üretilecek; ajanların tutarlı ve denetlenebilir bir yapıya ihtiyacı var.
- Dış bağımlılıklar: bulut LLM ve embedding API'leri, Qdrant, PostgreSQL. Testte bunların taklit edilebilmesi gerekiyor.
- Tek bir asenkron iş var: sayfaların arka planda indekslenmesi.

Ayrıntılı araştırma, 8 sistem stilinin ve 6 kod organizasyonu yaklaşımının karşılaştırması: [mimari-secimi.md](../mimari-secimi.md).

## Karar

- **Sistem stili:** Katmanlı **modüler monolit**. Tek backend süreci; indeksleme döngüsü aynı süreçte arka plan görevi olarak çalışır (ADR-005).
- **Kod yapısı:** Dört katman ve **içe doğru bağımlılık** (hocanın ProjectRouter örneğindeki yapı):

| Katman | Sorumluluk | Bağımlı olabileceği |
| --- | --- | --- |
| `domain` | Entity, value object, kurallar (R-xx) | Hiçbir şey |
| `application` | Servisler + **port arayüzleri** | `domain` |
| `infrastructure` | Port uygulamaları (PostgreSQL, Qdrant, LLM, güvenlik, indeksleme döngüsü) | `application`, `domain` |
| `api` | HTTP: router, şema, hata eşleme | `application`, `domain` |

- Bağımlılıklar `main.py` (composition root) içinde bağlanır.
- Kurallar **import-linter** ile CI'da zorunlu tutulur.
- Bilinçli olarak **yapılmayanlar:** use case başına sınıf, presenter, katman başına DTO zinciri, CQRS, Mediator, olay veriyolu, ayrı işçi servisi.

## Değerlendirilen alternatifler

| Alternatif | Neden seçilmedi |
| --- | --- |
| Mikroservisler / event-driven | Ölçek ihtiyacı yok; ağ, dağıtık tutarlılık ve broker karmaşıklığı. Bölüm 8: "gereksiz karmaşıklık borcu". |
| Service-based (2–3 servis) | En yakın alternatif; ama ayrı deploy'lar ve servisler arası HTTP 4 haftada ek yük getirir, tek ekip için kazancı yok. |
| Klasik 3 katman (lesson05) | Application somut veri katmanına bağlı kalır; LLM/Qdrant'ı testte taklit etmek zorlaşır. |
| Tam Clean Architecture | Özellik başına çok sınıf ve kavram; 4 haftada aşırı mühendislik. |
| Vertical Slice | Katman sınırı olmadığı için "mimari uyumu" kanıtlamak zor; ajanlarla kod tekrarı riski. |
| Düz FastAPI | Test edilemez, gösterilecek mimari yok. |

## Sonuçlar

**Avantajlar:**
- Basitlik ve düşük maliyet (Richards & Ford: Layered ★★★★★).
- Layered'ın zayıf yanı olan test edilebilirlik port'lar ve fake'lerle güçlenir.
- Yapay zeka sağlayıcısı veya vektör veritabanı değişirse yalnızca bir adaptör değişir.
- Mimari uyum otomatik ve kanıtlanabilir (sunumda `lint-imports` çıktısı).
- Tek süreç, tek `docker compose up`: kurulum ve demo basit.

**Değiş tokuşlar:**
- Basit bir CRUD için bile birkaç katmanda dosya açılır.
- Domain nesnesi ↔ veritabanı satırı eşleme kodu yazılır.
- İndeksleme döngüsü API ile aynı süreçte; API yeniden başlarken döngü de durur (durum veritabanında olduğu için iş kaybolmaz).
