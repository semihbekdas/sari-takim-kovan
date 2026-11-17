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
3. eşit büyüklükte Should işleri.

| Paket | Sahibi | Altyapı / ortak servis payı | Must | Should |
| --- | --- | --- | --- | --- |
| **İP-A Sayfalar & Editör** | **Umut** | docker-compose (PostgreSQL + Qdrant) + Alembic kurulumu, frontend iskeleti (Vite + React + TS, yönlendirme, ana yerleşim, API istemcisi) | Page aggregate (R-03, R-04, R-07, R-08), sayfa CRUD API'si, sol menü ağacı + breadcrumb, BlockNote editör (kısıtlı şema) + otomatik kaydetme + çakışma uyarısı (409), silme, `@` sayfa bağlantısı (editör tarafı) · F-05–F-10, F-15, F-17 | F-11 taşıma (R-05), F-12 çöp kutusu, F-13 son düzenlenenler |
| **İP-B Kimlik, İçerik & Arama** | **Özlem** | Arama servisi: anlamsal arama (R-12), yapay zeka port'larını kullanarak | `PageContent` (R-06), kayıt/giriş/çıkış (ADR-008) + ekranları, chunking (ADR-009), bağlantılar + geri bağlantılar (R-09) API'si ve paneli, kelime araması + arama ekranı (kelime ve anlamsal mod) · F-01–F-03, F-16, F-18, F-19 | F-04 rate limit, F-24 token loglama, Playwright duman testleri |
| **İP-C Yapay Zeka** | **Semih** | Backend iskeleti (uv, FastAPI, katman klasörleri, import-linter sözleşmeleri, yapılandırma, hata formatı, port düzeni) · CI (GitHub Actions: lint + test + import-linter) + SonarQube Cloud | Yapay zeka adaptörleri + fake mod (ADR-006), Qdrant adaptörü, indeksleme döngüsü (R-10, R-11) + indeks durumu, "Sayfalarına Sor" + kaynaklar (R-13) · F-20–F-23 | F-25 sohbet geçmişi, F-26 MCP server |
| **Ortak** | Herkes | — | RAG değerlendirme seti (herkes ~5 kurgusal sayfa + 7 soru yazar), embedding karşılaştırması (herkes bir adayı dener, ADR-006), güvenlik gözden geçirmesi, eksik testler, README, sunum | — |

**Review düzeni:** Her PR'ı, PR'ı açan kişi dışındaki en az bir ekip üyesi inceler; review'lar dönüşümlü yapılır. Böylece herkes diğer modülleri de tanır ve sunumda onlarla ilgili sorulara da cevap verebilir.

**Bağımlılıklar:** Backend iskeleti Sprint 1'in ilk günlerinde `main`'e girer, diğer backend işleri onun üzerine kurulur. Kimlik doğrulama bitene kadar sayfa API'si testlerde sabit bir test kullanıcısıyla geliştirilir. İskelet; katman yapısını, port düzenini (`application/ports/`), hata formatını ve sağlık uç noktalarını getirir. Her port, onu ilk kullanan özellikle birlikte eklenir (kullanılmayan kod commit'lenmez). Anlamsal arama (Özlem), yapay zeka ve Qdrant adaptörleri (Semih) gelene kadar fake'lerle geliştirilir.

## 4. Sprint takvimi

Sprintler Pazartesi başlar, hafta sonu toplantısıyla biter. Takvim **4 büyük sprinte** sıkıştırıldı: kod **13 Aralık**'ta donar, 14–25 Aralık sunum hazırlığı ve tampondur.

| Sprint | Tarih | Umut (İP-A) | Özlem (İP-B) | Semih (İP-C) |
| --- | --- | --- | --- | --- |
| **0** | 13 – 15 Kas | Doküman seti ve public repo | | |
| **1** Temel | 16 – 22 Kas | Doküman okuma PR'ı · docker-compose + Alembic · Frontend iskeleti | Doküman okuma PR'ı · `PageContent` (doğrulama, düz metin, bağlantı çıkarma) + birim testleri | Repo ayarları · Backend iskeleti · CI + SonarQube Cloud · Yapay zeka adaptörleri + fake mod |
| **2** | 23 – 29 Kas | Page domain + `pages` migration + sayfa CRUD API'si + kabul testleri · Sol menü ağacı + breadcrumb | Kayıt/giriş/çıkış API'si (Argon2, JWT çerez) + testleri · Chunking modülü | Qdrant adaptörü · İndeksleme döngüsü + indeks durumu + `reindex` CLI · CI'a frontend kontrolleri |
| **3** | 30 Kas – 6 Ara | BlockNote editör (kısıtlı şema) + otomatik kaydetme + 409 · Silme (R-08) | Giriş/kayıt ekranları · Anlamsal arama servisi · Kelime araması + arama ekranı (iki mod) | "Sayfalarına Sor" (backend + UI + kaynaklar) |
| **4** Bitiş | 7 – 13 Ara | `@` sayfa bağlantısı + `/pages/titles` · *(Should)* taşıma, çöp kutusu, son düzenlenenler | Bağlantılar + geri bağlantılar (API + panel) · *(Should)* rate limit, token loglama, Playwright duman testleri | *(Should)* sohbet geçmişi, MCP server · RAG parametre ayarı |
| | | **Ortak:** değerlendirme seti ve embedding karşılaştırması (Sprint 2) · güvenlik gözden geçirmesi (Sprint 3) · eksik testler, Sonar A, README (Sprint 4) · **13 Ara: kod dondurma** | | |
| **Sunum + tampon** | 14 – 25 Ara | README ekran görüntüleri ve sonuçlar, sunum taslağı, en az 2 prova (≤ 25 dk), yalnızca hata düzeltme · **25 Ara: teslim** | | |

**Kural:** Bir sprintin Must işleri bitmeden Should işlerine geçilmez. Sprint 3 sonunda Must'larda gecikme varsa Sprint 4'teki Should'lar kesilir.

**Commit hedefi:** Her üye her sprintte **≥ 3 commit** (en az 2 farklı günde), **≥ 1 PR** ve **≥ 1 review**.

## 5. Sprint 0: dokümanlar ve ilk PR'lar

- Doküman seti **14 Kasım'da tek bir başlangıç commit'iyle** `main`'e eklendi (ekip kararı: hız).
- Dengeyi korumak için **her üye kendi iş paketiyle ilgili dokümanları okur** ve düzeltme/ekleme yaparsa bunu **kendi branch'inden PR** ile gönderir (örn. `docs/mimari-duzeltmeleri`). Değişiklik yoksa `docs/ai-log.md`'ye "okundu" kaydını PR ile ekler.
- Böylece ilk PR'lar ve review'lar yine Sprint 0–1'de gelir; "en az 3 PR" şartı erken karşılanır.
- Sonraki sprintlerde commit dengesi iş paketleri üzerinden sağlanır (§ 3, § 4).

## 6. Riskler

| Risk | Olasılık | Etki | Önlem |
| --- | --- | --- | --- |
| Süre kısa (~4 hafta), dönem sonu sınavlarıyla çakışma | Yüksek | Yüksek | Kod dondurma 13 Ara + 12 gün tampon; MoSCoW; Should'lar kesilebilir |
| Kapsam şişmesi (Notion çok büyük) | Yüksek | Yüksek | "Won't" listesi; yeni özellik = toplantıda ekip onayı |
| **Anlama borcu** (yapay zekanın yazdığı kodu kimse okumuyor) | Yüksek | Yüksek | Zorunlu review, PR'da "ne/neden" açıklaması, sunum provası (ders Bölüm 15) |
| **API anahtarının public repoya sızması** | Orta | Yüksek | `.env` + `.gitignore`, GitHub push protection, CI'da gerçek anahtar yok, harcama limiti |
| API maliyeti / ücretsiz kota bitmesi (429) | Orta | Orta | Fake mod varsayılan, düzenleme bitince indeksleme, harcama limiti, 429 → yeniden deneme |
| Bulut sağlayıcı kesintisi demo sırasında | Düşük | Yüksek | Demo öncesi sağlık kontrolü; gerekirse `.env` ile ikinci sağlayıcıya geçiş; ekran kaydı yedeği |
| PostgreSQL ↔ Qdrant tutarsızlığı | Orta | Orta | Sürüm işaretli indeksleme + aramada PostgreSQL doğrulaması + `reindex` (ADR-005) |
| Dengesiz commit dağılımı | Orta | Yüksek | Dikey iş paketleri, haftalık `git shortlog` kontrolü |
| Üç ajanın ürettiği kodun çakışması | Orta | Orta | `AGENTS.md`, sabit port arayüzleri, kısa ömürlü branch'ler |
| Ekipte farklı teknoloji deneyimleri (web, React, Docker) | Orta | Orta | Kurulum adımları README'de; eşli çalışma (pair programming) oturumları; review'larla bilgi paylaşımı |

## 7. İlerleme

| Sprint | Durum | Not |
| --- | --- | --- |
| 0 | ✅ Tamamlandı | Doküman seti ve public repo (14 Kas) |
| 1 | 🟡 Devam ediyor | Görev dağılımı ve issue'lar (#2–#17, 16 Kas); backend iskeleti + CI + SonarQube (PR #1, kalite kapısı A; review düzeltmeleri 18 Kas); yapay zeka adaptörleri hazır (PR #1 merge olunca PR açılır); doküman tutarlılık düzeltmeleri (18 Kas). Takvim 4 büyük sprinte sıkıştırıldı |

## 8. Kriter skor kartı

Ders rehberindeki kriterlere göre her hafta sonu puanlanır (her kriter 0–10, ağırlıksız iç ölçek; hoca resmi ağırlık vermedi). Kriterlerin projedeki karşılıkları: [README § 12](../README.md#12-ders-kriterlerinin-karşılanması).

10/10 için gereken kanıt: **Takım** → commit/PR dengesi · **AI** → üründe + geliştirmede kullanım ve ai-log · **Süreç** → zamana yayılmış commit + ≥ 3 review'lu PR · **Teknik borç** → Sonar A · **Güvenlik** → tehdit modeli testleri · **Mimari** → import-linter yeşil + ADR'ler · **Okunabilirlik** → lint temiz, düşük karmaşıklık · **Test** → her Must AC'ye test, kapsam hedefleri · **Doküman** → README + docs güncel · **Veritabanı** → migration + entegrasyon testleri · **Sunum** → prova yapıldı, herkes kodunu anlatabiliyor.

| Tarih | Takım | AI | Süreç | T.Borç | Güvenlik | Mimari | Okunabilirlik | Test | Doküman | Veritabanı | Sunum | Toplam /110 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 13 Kas | 0 | 2 | 0 | 0 | 2 | 3 | 0 | 2 | 6 | 2 | 0 | **17** |
| 13 Kas (revizyon) | 0 | 2 | 0 | 0 | 2 | 4 | 0 | 2 | 7 | 2 | 0 | **19** |

*Not (13 Kas itibarıyla):* O tarihte kod ve commit yoktu; puanlar "planlandı ve belgelendi" düzeyinde. Revizyonda mimari araştırma dokümanı eklendi (Mimari +1, Doküman +1). En düşük kriterler (Süreç, Takım, Teknik Borç, Okunabilirlik) Sprint 0–1'in önceliği: repo + PR akışı + CI + Sonar + ilk kod.
