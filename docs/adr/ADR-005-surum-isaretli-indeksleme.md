# ADR-005: Sürüm İşaretli Arka Plan İndeksleme

## Durum

Kabul Edildi *(Accepted)* — 2026-11-13. *(İlk taslaktaki ayrı `index_jobs` tablolu outbox tasarımının sadeleştirilmiş halidir.)*

## Bağlam

Sayfa değişince vektör indeksinin (Qdrant) de güncellenmesi gerekir. Saf yaklaşım, yani kaydetme isteği içinde embedding alıp Qdrant'a yazmak, şu sorunları doğurur:

- **Maliyet:** Otomatik kaydetme yazarken ~1 sn'de bir çalışır. Her kayıtta ücretli embedding API'sini çağırmak gereksiz harcamadır.
- **Hız:** Embedding API'si yavaşsa kayıt yavaşlar.
- **Tutarlılık:** API veya Qdrant o an kapalıysa ya kayıt başarısız olur ya da PostgreSQL ile Qdrant birbirinden kopar (sayfa silinir ama vektörü kalır → silinen içerik sohbette görünür). ders Bölüm 8'deki yanılgı: "ağ güvenilirdir".

## Karar

İndeksleme ihtiyacı **sayfanın kendi satırında** tutulur ve tek bir arka plan döngüsü tarafından işlenir:

1. `pages` tablosunda `version` (her içerik/görünürlük değişikliğinde +1) ve `indexed_version` (Qdrant'a en son işlenen sürüm) vardır. `indexed_version IS DISTINCT FROM version` → sayfa "indeksleme bekliyor" (R-10). Hiç indekslenmemiş sayfada `indexed_version` NULL'dır; `≠` NULL ile karşılaştırmada sonuç vermediği için SQL'de `IS DISTINCT FROM` kullanılır. Bu bilgi sayfa güncellemesiyle **aynı satırda ve aynı transaction'da** yazıldığı için hiçbir değişiklik kaybolmaz.
2. Backend sürecinde çalışan **indeksleme döngüsü** ~5 sn'de bir şu sayfaları alır: indeksleme bekleyen, **en az 10 sn'dir düzenlenmeyen** (`INDEX_SETTLE_SECONDS`), deneme sayısı 5'in altında ve yeniden deneme zamanı gelmiş olanlar (en fazla 10 sayfa).
3. Her sayfa için okunan sürüm `v` ile:
   - Sayfa silinmişse → Qdrant'ta `page_id`'ye ait noktaları sil.
   - Değilse → parçala (ADR-009) → embedding al → `page_id`'nin eski noktalarını sil → yenilerini yaz.
   - Başarılıysa `indexed_version = v`, `index_attempts = 0`; `index_error` ve `index_retry_at` temizlenir.
   - Hata olursa `index_attempts + 1`, `index_error` (kısa özet) ve `index_retry_at = now + 5·2^n sn` (n: o ana kadarki başarısız deneme sayısı → 5, 10, 20, 40 sn). 5. başarısızlıkta durum `FAILED` (R-11). Sayfa tekrar düzenlenince sayaç ve bekleme sıfırlanır.
4. **Dış API çağrısı sırasında satır kilitlenmez.** İndeksleme sırasında yeni bir kayıt gelirse `version` yine `indexed_version`'dan büyük kalır ve sayfa bir sonraki turda tekrar işlenir (nihai tutarlılık).
5. **İdempotent:** Nokta kimlikleri `uuid5(page_id:chunk_no)`; aynı sürümün iki kez işlenmesi aynı sonucu verir.
6. **Silme anında görünmezlik:** Arama ve sohbet, Qdrant sonuçlarını PostgreSQL'den doğrular; silinmiş sayfalar indeksleme beklenmeden hemen elenir.
7. **Kurtarma:** `uv run python -m kovan.cli reindex --all` *(planlanan)* Qdrant koleksiyonunu PostgreSQL'den baştan üretir (embedding modeli değişince de kullanılır).
8. **Kalıcı silme** *(çöp kutusu, Should)*: Satırı silmeden önce sayfanın ve alt sayfalarının Qdrant noktaları silinir. Döngü yalnızca `pages` satırlarını gördüğü için, aksi halde vektörler öksüz kalırdı.

## Değerlendirilen alternatifler

| Alternatif | Neden seçilmedi |
| --- | --- |
| **Senkron indeksleme** (kayıt isteği içinde) | Her otomatik kayıtta ücretli API çağrısı, yavaş kayıt, dış servis hatasında tutarsızlık. |
| **FastAPI `BackgroundTasks`** | İş bellekte durur; süreç yeniden başlarsa veya hata olursa iş kaybolur, yeniden deneme yok. |
| **Ayrı `index_jobs` tablosu (klasik transactional outbox)** | Doğru ama bizim için fazla: iş türleri, birleştirme mantığı, kilitleme. Tek bir "sayfa sürümü" bilgisi aynı garantiyi daha az kodla veriyor. *(İlk taslakta bu vardı; aşırı mühendislik olarak sadeleştirildi.)* |
| **Mesaj kuyruğu** (RabbitMQ, Redis + Celery) | Yeni bir altyapı servisi; "veritabanına yazdım ama kuyruğa yazamadım" (dual write) sorununu da tek başına çözmez. |
| **pgvector ile tek veritabanı** | Tutarlılığı kolaylaştırırdı; ama ders içeriği ve önerisi Qdrant (ADR-004). |

## Sonuçlar

**Avantajlar:**
- Kayıt hızlıdır ve yapay zeka servisinin durumundan bağımsızdır.
- Yazma sırasında API çağrısı yok: sayfa başına, düzenleme bitince **bir** embedding çağrısı (maliyet).
- Hiçbir değişiklik kaybolmaz; geçici hatalar otomatik düzelir (ders Bölüm 8: **Retry**, **Idempotency**).
- Ek tablo, kuyruk veya kilit yok; tamamı birkaç fonksiyon ve testle anlatılabilir.
- Sunumda anlatılacak somut bir "zorluk ve çözüm" hikayesi.

**Değiş tokuşlar:**
- Anlamsal arama ve sohbet, düzenleme bittikten ~10–30 sn sonra güncel olur (AC-10.3).
- Tek döngü varsayımı: Backend birden çok kopya çalıştırılırsa satır kilitleme (`FOR UPDATE SKIP LOCKED`) eklenmelidir.
