# Yapay Zeka Kullanım Günlüğü — Semih

> Semih'in (İP-C) kayıtları. Şablon ve kurallar: [README.md](README.md). Kayıtlar tarih sırasıyla, en yenisi en altta.

### 2026-11-16 — Backend iskeleti (İP-C altyapı payı)
- **Kim:** Semih
- **Araç / model:** Claude Code (Claude Opus 5.5)
- **Amaç:** Katmanlı backend iskeletini kurmak: proje yapılandırması (uv), katman klasörleri, import-linter sözleşmeleri, ayarlar, JSON loglama + `request_id`, tek hata formatı, sağlık uç noktaları ve testleri.
- **Prompt (özet):** "Hocanın isterlerine bak, her şey hazırsa benim görevime başla." (Görev: docs/PLAN.md § 4, Sprint 1.)
- **Sonuç:** `backend/` klasörü. 20 test geçti (1 Docker testi Docker kapalı olduğu için atlandı), kapsam %96, ruff + mypy (strict) + import-linter (4/4 sözleşme) temiz.
- **Yapay zekanın hataları / eksikleri ve düzeltmeleri:**
  - İlk taslakta henüz kullanılmayan yapay zeka ve vektör port'ları da vardı → "kullanılmayan kod commit'lenmez" kuralına aykırı ve kapsamı %0 gösteriyordu → kaldırıldı; her port onu ilk kullanan özellikle eklenir.
  - Eşlemesi unutulmuş bir hata tipi 500 ile kendi mesajını döndürüyordu → iç ayrıntı sızdırmasın diye "beklenmeyen hata" gibi ele alındı, testi eklendi.
  - Eski kütüphane yolları uyarı veriyordu (`httpx` → `httpx2`, `testcontainers.postgres` → `testcontainers.community.postgres`) → güncellendi.
  - mypy test modülünü iki farklı adla buluyordu, ruff test fonksiyonunu fazla karmaşık buldu → yapılandırma ve test düzeni düzeltildi.
- **Bizim müdahalemiz:** ✍️ DOLDURULACAK *(kodu okuyunca değiştirdiğin veya sorduğun şeyler)*
- **Ders çıkarımı:** Otomatik kontroller (lint, tip, mimari, kapsam) yapay zekanın gözden kaçırdığı sorunları hemen yakaladı.

### 2026-11-16 — CI (GitHub Actions) ve SonarQube Cloud
- **Kim:** Semih
- **Araç / model:** Claude Code (Claude Opus 5.5)
- **Amaç:** Her PR'da lint, biçim, tip, mimari kurallar, testler ve kapsamı çalıştıran CI; analizin SonarQube Cloud'a gönderilmesi.
- **Sonuç:** `.github/workflows/ci.yml`, `sonar-project.properties`, README rozetleri. SonarQube Cloud organizasyonu/projesi ve `SONAR_TOKEN` secret'ı Semih tarafından tarayıcıdan oluşturuldu.
- **Kararlar:** SonarQube'un önerdiği örnek workflow yerine testleri ve kapsamı da içeren tek bir CI işi yazıldı. Action'lar güvenlik için sürüm etiketi yerine sabit commit SHA ile kullanıldı. "Automatic Analysis" kapatıldı (CI analiziyle çakışır).
- **Bizim müdahalemiz:** ✍️ DOLDURULACAK

### 2026-11-16 — İlk SonarQube analizi: güvenlik C → A
- **Kim:** Semih
- **Araç / model:** Claude Code (Claude Opus 5.5) + SonarQube Cloud
- **Ne oldu?** PR #1'in ilk analizinde kod koşulları geçti (kapsam %97.2, tekrar %0) ama **güvenlik derecesi C** olduğu için kalite kapısı kırmızı yandı.
- **Yapay zekanın hatası:** Yazdığı CI dosyasında `uv sync` paketlerin kurulum betiklerini çalıştırabiliyordu (`githubactions:S8541`), `uv run` adımları kilitli sürümlerden sapabiliyordu (`S8544`). Ayrıca `lifespan` içinde `yield` sonrası temizlik `try/finally` ile korunmamıştı (`python:S9152`).
- **Düzeltme:** `uv sync --locked --no-build --no-install-project`, `uv run --frozen --no-sync`, kod kaynaktan (`PYTHONPATH=src`) çalıştırıldı; `lifespan` `try/finally` ile sarıldı.
- **Sonuç:** Kalite kapısı geçti: güvenilirlik, güvenlik ve bakım kolaylığı **A**, kapsam %97.2, 0 açık bulgu. CI'da gerçek PostgreSQL ile 21/21 test.
- **Bizim müdahalemiz:** ✍️ DOLDURULACAK
- **Ders çıkarımı:** Ölçüm aracı, yapay zekanın "çalışan ama güvensiz" yazdığı yapılandırmayı yakaladı (Bölüm 5 ve 18). README'deki "Zorluklar" tablosuna eklendi.

### 2026-11-16 — Yapay zeka adaptörleri ve fake mod (İP-C)
- **Kim:** Semih
- **Araç / model:** Claude Code (Claude Opus 5.5)
- **Amaç:** ADR-006'daki port'lar (`EmbeddingProvider`, `ChatModel`) ve adaptörleri: Claude (resmi `anthropic` SDK), OpenAI uyumlu API'ler (OpenAI, Gemini, OpenRouter/bge-m3) ve API anahtarı gerektirmeyen fake mod; ayarlara göre doğru adaptörü kuran fabrika.
- **Sonuç:** `backend/src/kovan/infrastructure/ai/`, `application/ports/ai.py`. Adaptörler gerçek SDK'larla ama internete çıkmadan (sahte HTTP katmanı) test edildi; 44 test, kapsam %98.
- **Kararlar:**
  - Claude için modelin reddetmesi (refusal) durumunda sunucu taraflı yedek model (`fallbacks="default"`) açık; desteklemeyen modellerde yok sayılır.
  - Claude'da düşünme kapatılamadığı için maliyet `CHAT_EFFORT=low` ile kontrol ediliyor; `CHAT_MAX_TOKENS` düşünme token'larını da kapsadığı için 800 → 4096 yapıldı.
  - SDK sürümleri ezberden değil, kurulu paketin kaynak kodundan doğrulandı (`anthropic` 2.x, `openai` 3.x; ikisi de `httpx2` kullanıyor).
- **Yapay zekanın hataları ve düzeltmeleri:** `.env`'de boş bırakılan `CHAT_EFFORT=` uygulamanın açılmasını engelleyecekti → boş değerler "ayarlanmamış" sayıldı, testi eklendi. Claude mesaj tipleri için mypy belirsizlik hatası → açık tiplerle düzeltildi.
- **Bizim müdahalemiz:** ✍️ DOLDURULACAK

### 2026-11-18 — PR #1 review'u: Codex'in 5 uyarısı ve Özlem'in sorusu
- **Kim:** Semih (review: Özlem ve Codex otomatik review'u)
- **Araç / model:** Claude Code (Claude Opus 5.5)
- **Ne oldu?** PR #1'e Codex otomatik review'u 5 uyarı bıraktı. Özlem review'unda, Docker yokken entegrasyon testinin atlanmasının KURALLAR § 5'teki "`skip` yasak" kuralıyla çeliştiğini sordu ve diğer uyarılara da bakılmasını istedi.
- **Yapay zekanın hataları (review yakaladı):**
  1. Hata loglarına o andaki yerel değişkenler de yazılıyordu (structlog'da `show_locals` varsayılan olarak açık); şifre veya API anahtarı loga düşebilirdi.
  2. 5xx durumlu `HTTPException`'ın ayrıntısı istemciye gönderiliyordu.
  3. Hata veren istekler süre ve durum bilgisiyle loglanmıyordu.
  4. CI'da Docker bozulursa entegrasyon testi atlanıyor, CI yine yeşil yanabiliyordu.
  5. Fork veya Dependabot PR'larında token olmadığı için Sonar adımı CI'ı kırıyordu.
- **Düzeltme:** Yerel değişkenler loglanmıyor, SQL hata mesajlarına sorgu parametreleri yazılmıyor (`hide_parameters`). 5xx `HTTPException` genel `INTERNAL_ERROR` döndürüyor. Hata veren istekler 500 olarak loglanıyor. Docker CI'da zorunlu (yoksa test hata veriyor), yerelde atlanıyor; kural metni de buna göre netleştirildi. Sonar analizi secret'ı olmayan PR'larda çalışmıyor. Her düzeltme için, eski kodda düşen bir test eklendi; 27 test geçti (PostgreSQL entegrasyon testi Docker ile çalıştı).
- **Kararlar:** Hatanın mesajı ve satırları loglarda kalıyor (teşhis için gerekli, istemciye hiç gitmiyor); asıl risk olan yerel değişkenler ve SQL parametreleri kaldırıldı.
- **Bizim müdahalemiz:** ✍️ DOLDURULACAK
- **Ders çıkarımı:** İnsan review'u ve otomatik review birlikte, yapay zekanın "çalışan ama güvensiz" yazdığı ayrıntıları yakaladı.

### 2026-11-18 — Yapay zeka adaptörleri: repo incelemesi bulguları
- **Kim:** Semih
- **Araç / model:** Claude Code (Claude Opus 5.5), beş ayrı alt ajanla repo incelemesi
- **Yapay zekanın hataları (inceleme yakaladı):**
  1. `EMBEDDING_API_KEY` boşken OpenAI anahtarı, `EMBEDDING_BASE_URL` başka bir sağlayıcıyı gösterse bile oraya gönderiliyordu.
  2. SDK'ların varsayılan 2 yeniden denemesi yüzünden kullanıcı 503'ü ~90 sn sonra görebiliyordu.
  3. Fake embedding "İ" harfini yanlış bölüyordu ("İndeksler" ile "indeksler" hiç benzemiyordu).
  4. Fake sohbet modeli, uygulamanın fake modunda çağrı kaydını sınırsız büyütüyordu.
  5. Yorumlar gerçeği yansıtmıyordu: fabrikanın "composition root'tan çağrıldığı" yazıyordu ama henüz çağrılmıyor; port listesinde var olan `ai` "ileride" diye geçiyordu.
- **Düzeltme:** Anahtarlar göreve göre adlandırıldı (`CHAT_API_KEY`, `EMBEDDING_API_KEY`), birinin yerine diğerine düşülmüyor. SDK yeniden denemesi 1'e indirildi. Fake düzeltmeleri ve yorumlar güncellendi. AC-11.5'in adaptör kısmı (zaman aşımında kullanıcıya giden mesaj) teste bağlandı. 56 test geçti.
- **Bizim müdahalemiz:** ✍️ DOLDURULACAK

### 2026-11-19 — PR #20 review'u: Codex'in 6 uyarısı ve Özlem'in review'u
- **Kim:** Semih (review: Özlem ve Codex otomatik review'u)
- **Araç / model:** Claude Code (Claude Opus 5.5)
- **Yapay zekanın hataları (review yakaladı):**
  1. Sohbet adresi boşken SDK'lar ortamdaki `OPENAI_BASE_URL` / `ANTHROPIC_BASE_URL` değişkenini kullanıyordu; anahtar ve sorular Kovan'ın ayarlamadığı bir adrese gidebilirdi (Anthropic tarafını Codex söylemedi, denerken bulundu).
  2. Gemini bir cevabı engellediğinde cevap seçeneği veya mesaj gelmeyebiliyor; kod bu durumda çöküyordu (500).
  3. Claude'un "bağlam penceresi doldu" bitiş nedeni tam cevap gibi işaretleniyordu.
  4. `EMBEDDING_DIM` gibi sayısal ayarlar 0 veya negatif olabiliyordu; hata ancak ilk kullanımda çıkıyordu.
  5. Embedding hatası testi AC-10.5'e bağlı değildi.
  6. Adaptör açıklaması, kullanmadığımız yerel modelleri (LM Studio/Ollama) destekliyormuş gibi yazıyordu.
- **Düzeltme:** Adresler her zaman açıkça veriliyor. Engellenen cevap "reddetme", bağlam penceresi dolması "kesildi" sayılıyor. Sayısal ayarlar pozitif olmak zorunda. AC-10.5 etiketi ve kullanıcı mesajı testi eklendi. Yerel model iddiası kaldırıldı. Her biri için test eklendi; 62 test geçti.
- **Bizim müdahalemiz:** ✍️ DOLDURULACAK

### 2026-11-25 — Qdrant vektör indeksi (İP-C, #14)
- **Kim:** Semih
- **Araç / model:** Claude Code (Claude Opus 5.5)
- **Amaç:** `VectorIndex` port'u ve Qdrant adaptörü: koleksiyonu kurma ve doğrulama, sayfa parçalarını yazma, sayfa silme, **yalnızca sahibinin notlarında** arama; `/health/ready`'ye Qdrant kontrolü.
- **Sonuç:** `infrastructure/vector/qdrant_index.py`, `application/ports/vector.py`. Testler Docker gerektirmeyen bellek içi Qdrant ile; gerçek sunucu testi Testcontainers ile (CI'da).
- **Kararlar:** Nokta kimlikleri `uuid5(sayfa:parça)` ile deterministik (aynı sayfanın tekrar indekslenmesi kopya üretmez, AC-12.3). Koleksiyon zaten varsa boyutu `EMBEDDING_DIM` ile karşılaştırılır; farklıysa açık hata. Geçici Qdrant hataları (bağlantı, 429, 5xx) `VECTOR_STORE_UNAVAILABLE` (503) olur. Uygulama açılırken Qdrant'a bağlanmaya çalışmaz.
- **Yapay zekanın hataları / eksikleri:** İlk taslak sayfayı yeniden yazarken önce eski parçaları siliyordu; yazma başarısız olursa sayfa aramadan kayboluyordu. Kalıcı hatalar (400, 404) da "geçici kesinti" sayılıyordu. İkisi de kod incelemesinde bulundu.
- **Düzeltme:** Önce yeni parçalar yazılıyor, sonra fazla kalan eski parçalar siliniyor. Yalnızca bağlantı hatası, 429 ve 5xx geçici sayılıyor. Her biri için test eklendi.
- **Bizim müdahalemiz:** ✍️ DOLDURULACAK

### 2026-11-25 — Değerlendirme seti (Semih'in payı) ve ölçüm betiği (Ortak, #17)
- **Kim:** Semih
- **Araç / model:** Claude Code (Claude Opus 5.5)
- **Sonuç:** `eval/README.md` (herkesin kullanacağı biçim), `eval/dataset/semih/` (5 kurgusal sayfa), `eval/questions/semih.toml` (7 soru: 3 normal, 2 eşanlamlı, 1 notlarda yok, 1 prompt injection), `eval/compare_embeddings.py` (Hit@1, Hit@5, MRR ve "notlarda yok" eşiği için skor). Sayfa kimliği `üye/dosya-adı` (farklı üyelerin aynı adlı dosyaları karışmaz); hatalı soru dosyası açıklayıcı hatayla durur.
- **Gözlem:** Sahte (kelime tabanlı) embedding ile Hit@1 = 0.33; Türkçe ekler ("3NF'de", "değişti/yenilendi") kelime eşleşmesini bozuyor. Gerçek embedding modelinin neden gerekli olduğunu gösteren somut bir ölçüm.
- **Yapay zekanın hataları / eksikleri:** İlk taslak üç modeli üç ayrı hesapla karşılaştırmayı planlıyordu; ödev ölçeğinde gereksiz bulundu (PR #28). Betik artık tek modeli ölçüyor.
- **Bizim müdahalemiz:** ✍️ DOLDURULACAK

### 2026-11-27 — PR #29 review'u: Özlem'in 2 notu ve Codex'in 4 uyarısı (#17)
- **Kim:** Semih (review: Özlem ve Codex otomatik review'u)
- **Araç / model:** Claude Code (Claude Fable 5.2)
- **Yapay zekanın hataları (review yakaladı):**
  1. `sonar.exclusions` iki ayrı satırda kalıyordu; yalnızca sonuncusu geçerli olduğu için `backend/migrations/**` dışlaması kayboluyordu (Özlem).
  2. Türüyle uyuşmayan soru (ör. `normal` ama `expected_pages = []`) hata vermiyor, sessizce öteki gruba sayılıp metrikleri bozuyordu (Özlem ve Codex).
  3. Arama eşiği için raporlanan skor beklenen sayfanın değil, en yakın sayfanın skoruydu; beklenen sayfa 2.–5. sıradayken eşik yanlış seçilebilirdi.
  4. Betik `backend/` dışında durduğu için `ruff` ve `mypy` kapsamına girmiyordu.
  5. Betik her bölümü tek parça sayıyor; uygulama ise 1000 karakteri aşan bölümü bölüyor. Uzun bir bölümde ölçüm uygulamayı yansıtmazdı.
- **Düzeltme:** Dışlamalar tek satırda. Soru türü ile `expected_pages` uyumu kontrol ediliyor. Rapor beklenen sayfaların ortalama ve en düşük skorunu, her soru için de beklenen sayfanın skorunu veriyor. CI'da `ruff` ve `mypy` betiği de denetliyor. 1000 karakteri aşan bölümde betik duruyor; parça boyutunu bu setle ayarlama iddiası ADR-009 ve test stratejisinden çıkarıldı.
- **Bizim müdahalemiz:** ✍️ DOLDURULACAK
