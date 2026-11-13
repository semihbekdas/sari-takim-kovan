# Proje Planı

> Kapsam: [OZELLIKLER.md](../OZELLIKLER.md) · Kurallar: [KURALLAR.md](../KURALLAR.md) · Bu dosya **her hafta sonu toplantısında** güncellenir.

---

## 1. Hedef

**20 Aralık 2026**'ya kadar tüm **Must** özellikleri, ders kriterlerinin hepsini karşılayacak kalitede bitirmek: Sonar A, testli, dokümante, dengeli ve zamana yayılmış commit geçmişi. Zaman kalırsa **Should** özellikleri eklemek. 21–25 Aralık yalnızca sunum hazırlığı ve hata düzeltme için ayrılmıştır. **Teslim: 25 Aralık 2026 (Cuma).**

## 2. Varsayımlar ve kısıtlar

| Konu | Durum |
| --- | --- |
| Teslim | 25 Aralık 2026 (son gün). Hedef bitiş 20 Aralık. |
| Süre | ~5 haftalık geliştirme (16 Kasım – 20 Aralık) + Sprint 0 + 5 günlük tampon |
| Ekip | 3 kişi; herkes yapay zeka destekli geliştirme yapacak |
| Toplantılar | **Hafta sonu** (Cumartesi veya Pazar, ~45 dk) |
| Yapay zeka | Bulut API (Claude / GPT / Gemini + embedding sağlayıcısı); geliştirme ve testler varsayılan olarak **fake** modda, API anahtarı gerekmez |
| Repo | Public (GitHub), `sari-takim-kovan`; SonarQube Cloud ücretsiz |
| Takım | Sarı Takım |
| Değişiklikler | Süreç içinde hocaya sorular sorulacak; cevaba göre plan güncellenir |

## 3. İş paketleri (dengeli dağılım)

Her paket **dikey bir dilimdir**: Kendi backend'ini, frontend'ini, testini ve dokümanını içerir. Böylece herkes hem backend hem frontend commit'i atar ve sunumda kendi özelliğini baştan sona anlatabilir.

| Paket | Kapsam | Must | Should | Sahibi |
| --- | --- | --- | --- | --- |
| **İP-A Sayfalar** | Page aggregate (R-03, R-04, R-07, R-08), sayfa API'si, BlockNote editör (kısıtlı şema), otomatik kaydetme + 409, sol menü ağacı, breadcrumb, silme, kelime araması | F-05–F-10, F-18 | F-11 taşıma (R-05), F-12 çöp kutusu, F-13 son düzenlenenler, F-04 rate limit, Playwright duman testleri | *(dağıtılacak)* |
| **İP-B Bağlantılar & İndeksleme** | `PageContent` (R-06), bağlantılar + geri bağlantılar (R-09), `@` sayfa bağlantısı, chunking (ADR-009), Qdrant adaptörü, indeksleme döngüsü (R-10, R-11), indeks durumu UI, `reindex` CLI | F-15–F-17, F-20 | F-24 token loglama ve raporu, RAG parametre ayarı | *(dağıtılacak)* |
| **İP-C Kimlik & Yapay Zeka** | Kayıt/giriş/çıkış (ADR-008), yapay zeka adaptörleri + fake mod (ADR-006), anlamsal arama (R-12), "Sayfalarına Sor" + kaynaklar (R-13), RAG değerlendirme seti | F-01–F-03, F-19, F-21–F-23 | F-25 sohbet geçmişi, F-26 MCP server | *(dağıtılacak)* |
| **Ortak** | Dönüşümlü: backend/frontend iskeleti, docker-compose, CI, SonarQube Cloud, import-linter, README, sunum | — | — | Herkes |

> İP-B ve İP-C projenin yapay zeka tarafını oluşturur. Yazılım deneyimi en fazla olan üyenin bunlardan birini alması önerilir. Port arayüzleri (`VectorIndex`, `EmbeddingProvider`, `ChatModel`) Sprint 1 toplantısında birlikte sabitlenir; böylece İP-B ve İP-C fake'lerle birbirini beklemeden paralel çalışır.

## 4. Sprint takvimi

Sprintler Pazartesi başlar, hafta sonu toplantısıyla biter.

| Sprint | Tarih | Hedef | İş paketlerine göre çıktılar |
| --- | --- | --- | --- |
| **0** | 13 – 15 Kas | Hazırlık | Dokümanların ilk commit'i (14 Kas) ve her üyenin doküman okuma/düzeltme PR'ı (§ 5) · GitHub repo (public), branch koruması, secret scanning + push protection · Hocaya e-posta · Yapay zeka sağlayıcısı kararı ve harcama limiti · **İlk toplantı: iş paketi dağıtımı** |
| **1** | 16 – 22 Kas | Temel | **Ortak:** backend iskeleti (uv, FastAPI, katman klasörleri, import-linter), frontend iskeleti (Vite + React + TS), docker-compose, CI + SonarQube Cloud, port arayüzleri · **A:** Page domain + migration + CRUD API · **B:** `PageContent` doğrulama, düz metin, bağlantı çıkarma + testleri · **C:** kayıt/giriş/çıkış (API + ekranlar) |
| **2** | 23 – 29 Kas | Editör ve yapay zeka temeli | **A:** BlockNote (kısıtlı şema) + otomatik kaydetme + 409, ağaç + breadcrumb, silme · **B:** `page_links` + geri bağlantılar (API + panel), `@` bağlantısı, chunking modülü · **C:** Anthropic ve OpenAI uyumlu adaptörler + fake mod, hata eşleme (503), **embedding karşılaştırması** (3 aday, `eval/compare_embeddings.py`, ADR-006) ve seçim |
| **3** | 30 Kas – 6 Ara | İndeksleme ve arama | **A:** kelime araması + arama ekranı · **B:** Qdrant adaptörü, indeksleme döngüsü, indeks durumu UI, `reindex` CLI · **C:** anlamsal arama servisi + arama ekranında anlamsal mod |
| **4** | 7 – 13 Ara | RAG | **C:** "Sayfalarına Sor" (backend + UI + kaynaklar), değerlendirme seti v1 · **A:** *(Should)* taşıma, çöp kutusu, son düzenlenenler · **B:** dayanıklılık testleri, *(Should)* token loglama · **Ortak:** güvenlik gözden geçirmesi |
| **5** | 14 – 20 Ara | Kalite ve bitiş | **C:** *(Should)* sohbet geçmişi, MCP server (zaman kalırsa) · **A:** *(Should)* rate limit, Playwright duman testleri · **B:** değerlendirme sonuçları ve parametre ayarı · **Ortak:** eksik testler, Sonar A, README (zorluklar, sonuçlar, ekran görüntüleri), sunum taslağı · **20 Ara: kod dondurma** |
| **Tampon** | 21 – 25 Ara | Sunum | En az 2 sunum provası (≤ 25 dk), herkes diğer modüllerin sorularına hazırlık, yalnızca hata düzeltme · **25 Ara: teslim** |

**Kural:** Bir sprintin Must işleri bitmeden Should işlerine geçilmez. Sprint 4 sonunda Must'larda gecikme varsa Should'lar kesilir.

**Commit hedefi:** Her üye her sprintte **≥ 3 commit** (en az 2 farklı günde), **≥ 1 PR** ve **≥ 1 review**.

## 5. Sprint 0: dokümanlar ve ilk PR'lar

- Doküman seti **14 Kasım'da tek bir başlangıç commit'iyle** `main`'e eklendi (ekip kararı: hız).
- Dengeyi korumak için **her üye kendi iş paketiyle ilgili dokümanları okur** ve düzeltme/ekleme yaparsa bunu **kendi branch'inden PR** ile gönderir (örn. `docs/mimari-duzeltmeleri`). Değişiklik yoksa `docs/ai-log.md`'ye "okundu" kaydını PR ile ekler.
- Böylece ilk PR'lar ve review'lar yine Sprint 0–1'de gelir; "en az 3 PR" şartı erken karşılanır.
- Sonraki sprintlerde commit dengesi iş paketleri üzerinden sağlanır (§ 3, § 4).

## 6. Riskler

| Risk | Olasılık | Etki | Önlem |
| --- | --- | --- | --- |
| Süre kısa (~5 hafta), dönem sonu sınavlarıyla çakışma | Yüksek | Yüksek | Hedef 20 Ara + 5 gün tampon; MoSCoW; Should'lar kesilebilir |
| Kapsam şişmesi (Notion çok büyük) | Yüksek | Yüksek | "Won't" listesi; yeni özellik = toplantıda ekip onayı |
| **Anlama borcu** (yapay zekanın yazdığı kodu kimse okumuyor) | Yüksek | Yüksek | Zorunlu review, PR'da "ne/neden" açıklaması, sunum provası (Bölüm 15) |
| **API anahtarının public repoya sızması** | Orta | Yüksek | `.env` + `.gitignore`, GitHub push protection, CI'da gerçek anahtar yok, harcama limiti |
| API maliyeti / ücretsiz kota bitmesi (429) | Orta | Orta | Fake mod varsayılan, düzenleme bitince indeksleme, harcama limiti, 429 → yeniden deneme |
| Bulut sağlayıcı kesintisi demo sırasında | Düşük | Yüksek | Demo öncesi sağlık kontrolü; gerekirse `.env` ile ikinci sağlayıcıya geçiş; ekran kaydı yedeği |
| PostgreSQL ↔ Qdrant tutarsızlığı | Orta | Orta | Sürüm işaretli indeksleme + aramada PostgreSQL doğrulaması + `reindex` (ADR-005) |
| Dengesiz commit dağılımı | Orta | Yüksek | Dikey iş paketleri, haftalık `git shortlog` kontrolü |
| Üç ajanın ürettiği kodun çakışması | Orta | Orta | `AGENTS.md`, sabit port arayüzleri, kısa ömürlü branch'ler |
| Elektronik bölümü arkadaşların web deneyiminin az olması | Orta | Orta | Dikey paketlerde UI küçük; eşli çalışma (pair programming) oturumları |

## 7. İlerleme

| Sprint | Durum | Not |
| --- | --- | --- |
| 0 | 🟡 Devam ediyor | Dokümanlar hazır ve gözden geçirildi (13 Kas); repo ve dağıtım bekliyor |

## 8. Kriter skor kartı

Ders rehberindeki kriterlere göre her hafta sonu puanlanır (her kriter 0–10, ağırlıksız iç ölçek; hoca resmi ağırlık vermedi). Kriterlerin projedeki karşılıkları: [README § 12](../README.md#12-ders-kriterlerinin-karşılanması).

10/10 için gereken kanıt: **Takım** → commit/PR dengesi · **AI** → üründe + geliştirmede kullanım ve ai-log · **Süreç** → zamana yayılmış commit + ≥ 3 review'lu PR · **Teknik borç** → Sonar A · **Güvenlik** → tehdit modeli testleri · **Mimari** → import-linter yeşil + ADR'ler · **Okunabilirlik** → lint temiz, düşük karmaşıklık · **Test** → her Must AC'ye test, kapsam hedefleri · **Doküman** → README + docs güncel · **Veritabanı** → migration + entegrasyon testleri · **Sunum** → prova yapıldı, herkes kodunu anlatabiliyor.

| Tarih | Takım | AI | Süreç | T.Borç | Güvenlik | Mimari | Okunabilirlik | Test | Doküman | Veritabanı | Sunum | Toplam /110 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 13 Kas | 0 | 2 | 0 | 0 | 2 | 3 | 0 | 2 | 6 | 2 | 0 | **17** |
| 13 Kas (revizyon) | 0 | 2 | 0 | 0 | 2 | 4 | 0 | 2 | 7 | 2 | 0 | **19** |

*Not:* Henüz kod ve commit yok; puanlar "planlandı ve belgelendi" düzeyinde. Revizyonda mimari araştırma dokümanı eklendi (Mimari +1, Doküman +1). En düşük kriterler (Süreç, Takım, Teknik Borç, Okunabilirlik) Sprint 0–1'in önceliği: repo + PR akışı + CI + Sonar + ilk kod.
