# Proje Planı

> Kapsam: [OZELLIKLER.md](../OZELLIKLER.md) · Kurallar: [KURALLAR.md](../KURALLAR.md) · Bu dosya **her hafta sonu toplantısında** güncellenir.

---

## 1. Hedef

**13 Aralık 2026**'ya kadar tüm **Must** özellikleri, ders kriterlerinin hepsini karşılayacak kalitede bitirmek: Sonar A, testli, dokümante, dengeli ve zamana yayılmış commit geçmişi. Zaman kalırsa **Should** özellikleri eklemek. 14–25 Aralık yalnızca sunum hazırlığı ve hata düzeltme için ayrılmıştır. **Teslim: 25 Aralık 2026 (Cuma).**

## 2. Varsayımlar ve kısıtlar

| Konu | Durum |
| --- | --- |
| Teslim | 25 Aralık 2026 (son gün). Kod dondurma 13 Aralık. |
| Süre | 4 büyük sprint (16 Kasım – 13 Aralık) + Sprint 0 + 12 günlük sunum/tampon |
| Ekip | 3 kişi; herkes yapay zeka destekli geliştirme yapacak |
| Toplantılar | **Hafta sonu** (Cumartesi veya Pazar, ~45 dk) |
| Yapay zeka | Bulut API (Claude / GPT / Gemini + embedding sağlayıcısı); geliştirme ve testler varsayılan olarak **fake** modda, API anahtarı gerekmez |
| Repo | Public (GitHub), `sari-takim-kovan`; SonarQube Cloud ücretsiz |
| Takım | Sarı Takım |
| Değişiklikler | Süreç içinde hocaya sorular sorulacak; cevaba göre plan güncellenir |

## 3. İş paketleri ve görev dağılımı

İş yükü **eşit** dağıtıldı; paketler kabaca aynı büyüklükte tutuldu. Herkes üç tür iş alır:
1. bir altyapı veya ortak servis işi,
2. bir **dikey özellik paketi** (kendi backend'i, frontend'i, testi ve dokümanıyla; sunumda baştan sona anlatılabilir),
3. zaman kalırsa bir Should işi (§ 4'teki kural).

| Paket | Sahibi | Altyapı / ortak servis payı | Must | Should |
| --- | --- | --- | --- | --- |
| **İP-A Sayfalar & Editör** | **Umut** | docker-compose (PostgreSQL + Qdrant) + Alembic kurulumu, frontend iskeleti (Vite + React + TS, yönlendirme, ana yerleşim, API istemcisi) | Page aggregate (R-03, R-04, R-07, R-08), sayfa CRUD API'si, sol menü ağacı + breadcrumb, BlockNote editör (kısıtlı şema) + otomatik kaydetme + çakışma uyarısı (409), silme, `@` sayfa bağlantısı ve silinmiş sayfa gösterimi · F-05–F-10, F-15, F-17 | F-11 taşıma (R-05), F-12 çöp kutusu, F-13 son düzenlenenler |
| **İP-B Kimlik, İçerik & Arama** | **Özlem** | Anlamsal arama uç noktası (R-12), Semih'in parça getirme servisini kullanarak | `PageContent` (R-06), kayıt/giriş/çıkış (ADR-008) + ekranları, chunking (ADR-009), anlamsal arama uç noktası + arama ekranı · F-01–F-03, F-19 | F-16 geri bağlantılar (R-09), F-18 kelime araması, F-04 rate limit, F-24 token loglama |
| **İP-C Yapay Zeka** | **Semih** | Backend iskeleti (uv, FastAPI, katman klasörleri, import-linter sözleşmeleri, yapılandırma, hata formatı, port düzeni) · CI (GitHub Actions: lint + test + import-linter) + SonarQube Cloud | Yapay zeka adaptörleri + fake mod (ADR-006), Qdrant adaptörü, indeksleme döngüsü (R-10, R-11) + indeks durumu, parça getirme servisi, "Sayfalarına Sor" + kaynaklar (R-13) · F-20–F-23 | F-25 sohbet geçmişi |
| **Ortak** | Herkes | — | RAG değerlendirme seti (herkes ~5 kurgusal sayfa + 7 soru yazar) ve seçilen embedding modelinin bu setle ölçülmesi (ADR-006), güvenlik gözden geçirmesi, eksik testler, README, sunum | — |

**Review düzeni:** Her PR'ı, PR'ı açan kişi dışındaki en az bir ekip üyesi inceler; review'lar dönüşümlü yapılır. Böylece herkes diğer modülleri de tanır ve sunumda onlarla ilgili sorulara da cevap verebilir.

**Bağımlılıklar:** Backend iskeleti Sprint 1'in ilk günlerinde `main`'e girer, diğer backend işleri onun üzerine kurulur. Kimlik doğrulama bitene kadar sayfa API'si testlerde sabit bir test kullanıcısıyla geliştirilir. İskelet; katman yapısını, port düzenini (`application/ports/`), hata formatını ve sağlık uç noktalarını getirir. Her port, onu ilk kullanan özellikle birlikte eklenir (kullanılmayan kod commit'lenmez). Parça getirme (soruyu vektöre çevirme, Qdrant araması, silinmiş sayfaların elenmesi) tek yerde yazılır (Semih); anlamsal arama uç noktası (Özlem) ve "Sayfalarına Sor" aynı servisi kullanır. `users` tablosunun migration'ı Sprint 2'nin ilk PR'ıdır; `pages` migration'ı onun üzerine gelir.

## 4. Sprint takvimi

Sprintler Pazartesi başlar, hafta sonu toplantısıyla biter. Takvim **4 büyük sprinte** sıkıştırıldı: kod **13 Aralık**'ta donar, 14–25 Aralık sunum hazırlığı ve tampondur.

| Sprint | Tarih | Umut (İP-A) | Özlem (İP-B) | Semih (İP-C) |
| --- | --- | --- | --- | --- |
| **0** | 13 – 15 Kas | Doküman seti ve public repo | | |
| **1** Temel | 16 – 22 Kas | Doküman okuma PR'ı · docker-compose + Alembic · Frontend iskeleti | Doküman okuma PR'ı · `PageContent` (doğrulama, düz metin, bağlantı çıkarma) + birim testleri | Repo ayarları · Backend iskeleti · CI + SonarQube Cloud · Yapay zeka adaptörleri + fake mod |
| **2** | 23 – 29 Kas | Page domain + `pages` migration + sayfa CRUD API'si + kabul testleri · Sol menü ağacı + breadcrumb | `users` tablosu · Kayıt/giriş/çıkış API'si (Argon2, JWT çerez) + testleri · Chunking modülü | Qdrant adaptörü · İndeksleme döngüsü + indeks durumu · CI'a frontend kontrolleri |
| **3** | 30 Kas – 6 Ara | BlockNote editör (kısıtlı şema) + otomatik kaydetme + 409 · Silme (R-08) | Giriş/kayıt ekranları · Anlamsal arama uç noktası + arama ekranı | Parça getirme servisi · "Sayfalarına Sor" (backend + UI + kaynaklar) |
| **4** Bitiş | 7 – 13 Ara | `@` sayfa bağlantısı (başlıklar sayfa ağacından) · README ekran görüntüleri | AC ↔ test tablosu · eksik AC testlerinin takibi | RAG değerlendirmesi ve parametre ayarı · README sonuçları |
| | | **Ortak:** değerlendirme seti (Sprint 2) · güvenlik gözden geçirmesi (Sprint 3) · Sonar A, README (Sprint 4) · *(Should, zaman kalırsa)* kişi başı en fazla bir iş · **13 Ara: kod dondurma** | | |
| **Sunum + tampon** | 14 – 25 Ara | README ekran görüntüleri ve sonuçlar, sunum taslağı, en az 2 prova (≤ 25 dk), yalnızca hata düzeltme · **25 Ara: teslim** | | |

**Kural:** Should işlerine ancak bütün Must'lar, testleri ve README bittikten sonra başlanır. Kişi başı en fazla bir Should işi alınır; katkı dengesi için öncelik o ana kadar commit'i az olan üyededir. 10 Aralık'tan sonra yeni Should işine başlanmaz. Sprint 4 bu yüzden büyük ölçüde tampondur.

**Commit hedefi:** Her üye her sprintte **≥ 3 commit** (en az 2 farklı günde), **≥ 1 PR** ve **≥ 1 review**.

## 5. Sprint 0: dokümanlar ve ilk PR'lar

- Doküman seti **14 Kasım'da tek bir başlangıç commit'iyle** `main`'e eklendi (ekip kararı: hız).
- Dengeyi korumak için **her üye kendi iş paketiyle ilgili dokümanları okur** ve düzeltme/ekleme yaparsa bunu **kendi branch'inden PR** ile gönderir (örn. `docs/mimari-duzeltmeleri`). Değişiklik yoksa kendi `docs/ai-log/<isim>.md` dosyasına "okundu" kaydını PR ile ekler.
- Böylece ilk PR'lar ve review'lar yine Sprint 0–1'de gelir; "en az 3 PR" şartı erken karşılanır.
- Sonraki sprintlerde commit dengesi iş paketleri üzerinden sağlanır (§ 3, § 4).

## 6. Riskler

| Risk | Olasılık | Etki | Önlem |
| --- | --- | --- | --- |
| Süre kısa (~4 hafta), dönem sonu sınavlarıyla çakışma | Yüksek | Yüksek | Kod dondurma 13 Ara + 12 gün tampon; MoSCoW; Should'lar kesilebilir |
| Kapsam şişmesi (Notion çok büyük) | Yüksek | Yüksek | "Won't" listesi; yeni özellik = toplantıda ekip onayı; 22 Kasım'da kapsam daraltıldı (§ 7) |
| **Anlama borcu** (yapay zekanın yazdığı kodu kimse okumuyor) | Yüksek | Yüksek | Zorunlu review, PR'da "ne/neden" açıklaması, sunum provası (ders Bölüm 15) |
| **API anahtarının public repoya sızması** | Orta | Yüksek | `.env` + `.gitignore`, GitHub push protection, CI'da gerçek anahtar yok, harcama limiti |
| API maliyeti / ücretsiz kota bitmesi (429) | Orta | Orta | Fake mod varsayılan, düzenleme bitince indeksleme, harcama limiti, 429 → yeniden deneme |
| Bulut sağlayıcı kesintisi demo sırasında | Düşük | Yüksek | Demo öncesi sağlık kontrolü; gerekirse `.env` ile ikinci sağlayıcıya geçiş; ekran kaydı yedeği |
| PostgreSQL ↔ Qdrant tutarsızlığı | Orta | Orta | Sürüm işaretli indeksleme + aramada PostgreSQL doğrulaması + indeksin PostgreSQL'den yeniden üretilebilmesi (ADR-005) |
| Dengesiz commit dağılımı | Orta | Yüksek | Dikey iş paketleri, haftalık `git shortlog` kontrolü, ortak işlerde önceliğin commit'i az olan üyeye verilmesi |
| Üç ajanın ürettiği kodun çakışması | Orta | Orta | `AGENTS.md`, sabit port arayüzleri, kısa ömürlü branch'ler |
| Ekipte farklı teknoloji deneyimleri (web, React, Docker) | Orta | Orta | Kurulum adımları README'de; eşli çalışma (pair programming) oturumları; review'larla bilgi paylaşımı |

## 7. İlerleme

| Sprint | Durum | Not |
| --- | --- | --- |
| 0 | ✅ Tamamlandı | Doküman seti ve public repo (14 Kas) |
| 1 | ✅ Bitti (22 Kas) | `main`'de: backend iskeleti + CI + SonarQube Cloud (PR #1, kalite kapısı A), doküman tutarlılık düzeltmeleri (PR #19), yapay zeka adaptörleri ve fake mod (PR #20), doküman okuma (PR #18). 22 Kasım itibarıyla onaylanmış ve merge bekleyen: doküman okuma (PR #22), docker-compose + Alembic (PR #23), frontend iskeleti (PR #24). `PageContent` (PR #21) incelemede; Sprint 2'nin ilk işi olarak tamamlanacak. Takvim 16 Kasım'da 4 büyük sprinte sıkıştırıldı |
| 2 | ⏳ 23 Kas'ta başlıyor | **Kapsam daraltıldı (22 Kas).** Ölçüt: ders rehberindeki değerlendirme kriterleri ve P0007 tanımı (blok tabanlı sayfalar, sayfalar arası bağlantı, anlamsal arama, RAG). İkisinin de gerektirmediği işler ertelendi: Geri bağlantılar (F-16) ve kelime araması (F-18) Should'a, MCP server (F-26) ve Playwright testleri Could'a alındı; `/pages/titles` uç noktası ve `reindex` komutu plandan çıkarıldı. Embedding modeli seçildi: `text-embedding-3-small` (ADR-006). Kazanılan süre testlere ve Sprint 4 tamponuna ayrıldı |

## 8. Kriterlerin takibi

Ders rehberindeki her kriterin projedeki karşılığı ve kanıtı [README § 12](../README.md#12-ders-kriterlerinin-karşılanması)'de tutulur. Her hafta sonu toplantısında o tablo üzerinden eksikler konuşulur; sonuç yukarıdaki "İlerleme" tablosuna yazılır.
