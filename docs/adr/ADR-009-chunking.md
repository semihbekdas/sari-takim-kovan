# ADR-009: Parçalama (Chunking) Stratejisi — Başlık Farkındalıklı Parçalama

## Durum

Kabul Edildi *(Accepted)* — 2026-11-13

## Bağlam

- RAG kalitesi büyük ölçüde parçalama stratejisine bağlıdır (Bölüm 9: *"embedding modeline ve seçilen parçalama stratejisine bağlıdır"*).
- Derste **sabit karakter sayısına göre** bölme kullanıldı (lesson07: 500 karakter, 50 örtüşme). Bu yöntem cümleleri ve başlık bağlamını ortadan böler.
- Bizim içeriğimiz yapılandırılmış: BlockNote blokları ve başlık hiyerarşisi elimizde.
- Parçalama fonksiyonu deterministik ve kolay test edilebilir olmalı; aşırı karmaşık olmamalı.

## Karar

`application/chunking.py` içinde **saf fonksiyon** `chunk_page(title, content)`. Her parça `heading_path` ve `text` alanlarını taşır; bunlar indekslemede vektöre çevrilip Qdrant noktası olur (`domain-design.md` § 6):

1. İçerik başlıklara (H1–H3) göre **bölümlere** ayrılır; her bölüm `heading_path` taşır (`Sayfa › Başlık › Alt başlık`). Başlıksız içerik sayfa başlığının altında tek bölümdür.
2. Bir bölümün blokları sırayla bir parçaya eklenir; parça **`CHUNK_MAX_CHARS` (varsayılan 1000)** karakteri aşacaksa yeni parça başlar. Bloklar normalde bölünmez; yalnızca tek başına `CHUNK_MAX_CHARS`'ı aşan bir blok sabit uzunlukta parçalara bölünür.
3. İndeksleme sırasında embedding'e giden metnin başına bağlam başlığı eklenir (`chunk_page` ham metni döndürür): `"{heading_path}\n\n{metin}"`. Böylece "3NF" geçen bir paragraf "Veritabanı › Normalizasyon" bağlamını da taşır.
4. Boş sayfa → parça yok (indeks temizlenir).

`CHUNK_MAX_CHARS` RAG değerlendirme setiyle ayarlanır; seçilen değer ve ölçüm sonucu README'ye yazılır.

## Değerlendirilen alternatifler

| Alternatif | Neden seçilmedi |
| --- | --- |
| **Sabit karakter penceresi** (ders örneği) | Basit ama cümleleri ve başlık bağlamını böler; yapılandırılmış içeriğimizin avantajını kullanmaz. *(Could: değerlendirmede karşılaştırma tabanı olarak denenebilir.)* |
| **Örtüşmeli parçalar, kod bloğuna özel kurallar, cümle sınırından bölme** | Kaliteyi biraz artırabilir ama kodu ve test sayısını büyütür. Ölçüm ihtiyaç gösterirse eklenir (ilk taslaktan sadeleştirildi). |
| **Token tabanlı bölme** | Sağlayıcıya göre değişen tokenizer'a bağımlılık; karakter sınırı yeterli. |
| **Anlamsal parçalama** (embedding benzerliğine göre) | Her kayıtta ek embedding maliyeti; bu ölçekte gereksiz. |
| **Sayfa = tek parça** | Uzun sayfalarda alakasız içerik bağlamı doldurur ("lost in the middle"). |

## Sonuçlar

**Avantajlar:**
- Parçalar anlamsal olarak bütün; kaynak gösterimi başlık düzeyinde ("Veritabanı › Normalizasyon").
- Saf fonksiyon → kolay birim testleri (başlıksız sayfa, çok uzun blok, boş sayfa, Türkçe karakterler).
- Az parametre, kolay anlatılır.

**Değiş tokuşlar:**
- Ders örneğine göre biraz daha fazla kod.
- Parametre değişince tüm sayfaların yeniden indekslenmesi gerekir (`reindex --all`).
