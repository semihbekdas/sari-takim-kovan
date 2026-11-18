# Yapay Zeka Kullanım Günlüğü

> Ders kriteri: *"Kullanılan yapay zeka araçları ve kullanım şekli proje dokümantasyonunda açıkça belirtilmelidir."*
> Bu günlük README'deki **"Kullanılan Yapay Zeka Araçları"** ve **"Karşılaşılan Zorluklar ve Çözümler"** bölümlerinin kaynağıdır. Önemli her yapay zeka etkileşimi buraya kısa bir kayıt olarak eklenir.

## Kayıt şablonu

```markdown
### YYYY-AA-GG — <kısa başlık>
- **Kim:** <üye>
- **Araç / model:** <Claude Code (model), Copilot, …>
- **Amaç:** <ne yaptırıldı>
- **Prompt (özet veya tamamı):** <…>
- **Sonuç:** <ne üretildi, hangi dosyalar/PR>
- **Yapay zekanın hataları / eksikleri:** <…>
- **Bizim müdahalemiz:** <neyi düzelttik, neden>
- **Ders çıkarımı:** <bir dahakine ne yaparız>
```

---

## Kayıtlar

> **📝 `✍️ DOLDURULACAK` yazan yerler ne demek?** Aşağıdaki kayıtlarda yapay zekanın ne ürettiği yazılı, ama **sizin ne yaptığınız** henüz yazılı değil, çünkü henüz bir şey yapmadınız. Ders "Agentic Engineering" istiyor: Yapay zekanın çıktısını okumak, yanlışını bulmak, düzeltmek. Bu alanlar o işin kanıtı.
> - **Kim:** Claude Code oturumunu yürüten üyenin adı.
> - **Bizim müdahalemiz:** Dokümanları okuyunca neyi değiştirdiniz, neyi sildiniz, neye itiraz ettiniz? Örnek: *"Sprint 3'ü fazla yüklü bulduk, kelime aramasını Sprint 2'ye aldık."* veya *"İsim önerisini 'sari-takim-kovan' olarak kesinleştirdik."* Hiçbir şey değiştirmediyseniz "okundu, değişiklik yok" yazın. Boş bırakmayın.
> - Her üye, Sprint 1'deki doküman okuma PR'ında kendi iş paketinin dokümanlarını okuyup bu günlüğe ayrı bir kayıt ekler (PLAN § 5).

### 2026-11-13 — Ders reposunun analizi ve proje dokümanlarının taslağı
- **Kim:** ✍️ DOLDURULACAK *(oturumu yürüten üye)*
- **Araç / model:** Claude Code (Claude Opus 5.5)
- **Amaç:** Ders reposundaki (`buraksenyurt/ai-based-development-lecture`) proje kriterlerini, örnek projeleri (lesson01, lesson05 ADR'leri, ProjectRouter, lesson07/08 RAG örnekleri) incelemek; P0007 için mimari, plan, kurallar, kullanıcı hikayeleri ve ADR taslaklarını oluşturmak.
- **Prompt (özet):** "Notion ile başlayalım, dokümanları hazırla; önce hocanın reposundaki proje ile ilgili kısımları detaylıca incele, sonra hangi mimariyi neden kullandığımızı, planımızı, README'yi oluştur; ayrıca uygulama özelliklerini ve kuralları ayrı dosyalara yaz."
- **Sonuç:** `README.md`, `OZELLIKLER.md`, `KURALLAR.md`, `AGENTS.md`, `CLAUDE.md`, `docs/*` ve `docs/adr/ADR-001…010` taslakları.
- **Yapay zekanın hataları / eksikleri:** Bu taslağın hataları aynı gün yapılan revizyonda bulundu, bkz. bir sonraki kayıt. Sizin bulduklarınızı da buraya ekleyin.
- **Bizim müdahalemiz:** ✍️ DOLDURULACAK *(üyelerin doküman okuma kayıtları ayrı girdilerdedir)*
- **Ders çıkarımı:** Kod yazdırmadan önce mimari ve domain dokümanı hazırlamak (Bölüm 2 yaklaşımı) ajanlara tutarlı bağlam sağlar.

### 2026-11-13 — Dokümanların yeni kararlara göre revizyonu ve aşırı mühendislik kontrolü
- **Kim:** ✍️ DOLDURULACAK *(oturumu yürüten üye)*
- **Araç / model:** Claude Code (Claude Opus 5.5)
- **Amaç:** Yeni kararları işlemek (teslim 25 Aralık, hedef 20 Aralık; hafta sonu toplantıları; public repo; bulut dil modeli; çöp kutusu Should), mimari seçimini detaylı araştırmak, tüm dokümanları hata ve aşırı mühendislik açısından baştan kontrol etmek.
- **Sonuç:** `docs/mimari-secimi.md` eklendi; ADR-005 ve ADR-006 yeniden yazıldı; plan 5 haftaya göre yeniden kuruldu; tüm dokümanlar güncellendi.
- **Yapay zekanın ilk taslaktaki hataları / eksikleri (kendi kontrolünde buldu):**
  - Yerel model (LM Studio) varsayılmıştı; ekipte güçlü bilgisayar olmayabilir → bulut API + anahtarsız "fake" mod.
  - **Claude'un embedding modeli olmadığı** hesaba katılmamıştı → sohbet ve embedding sağlayıcıları ayrıldı (Anthropic dokümanı Voyage AI öneriyor).
  - BlockNote varsayılan olarak tablo/görsel/video blokları da sunuyor; backend bunları reddedeceği için kullanıcı 422 alırdı → editör şeması kısıtlandı.
  - Stil (renk vb.) beyaz listesi, editörün ürettiği geçerli içeriği reddederdi → stiller serbest bırakıldı.
  - Her otomatik kayıtta (~1 sn) embedding çağrılacaktı → bulut API'de gereksiz maliyet → "düzenleme 10 sn durunca indeksle".
  - İndeksleme işçisi dış API çağrısı sırasında satırı kilitleyecekti → otomatik kayıt bekleyecekti → kilitsiz tasarım.
  - Plan 8 Ocak'a göre 8 haftaydı → 20 Aralık hedefli 5 haftaya indirildi.
- **Aşırı mühendislik olarak sadeleştirilenler:** ayrı `index_jobs` outbox tablosu → sayfa satırında sürüm işareti; SQLAlchemy ORM + eşleme → SQLAlchemy Core; unit of work kaldırıldı; kardeş sayfa sıralaması (`position`) ve maksimum derinlik kuralı kaldırıldı; parçalamadaki örtüşme ve özel kurallar kaldırıldı; MSW kaldırıldı; 10 uçtan uca test → 3 duman testi (Should); sohbet oturumu Must'tan Should'a; favori/ikon Won't.
- **Bizim müdahalemiz:** Kararları ekip verdi: teslim 25 Aralık / hedef 20 Aralık, hafta sonu toplantıları, public repo, bulut dil modeli, çöp kutusunun Should olması, takım adı "Sarı Takım". ✍️ Dokümanları okuyunca yaptığınız ek düzeltmeleri buraya ekleyin.
- **Ders çıkarımı:** Yapay zekanın ilk ürettiği tasarım "doğru ama fazla" olabiliyor. Kısıtları (süre, ekip, bütçe) açıkça verip çıktıyı aşırı mühendislik açısından ayrıca sorgulamak gerekiyor.


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

### 2026-11-18 — PR #1 review'u: Codex'in 5 uyarısı ve Özlem'in sorusu
- **Kim:** Özlem
- **Araç / model:** Claude (claude.ai, Claude Code)
- **Amaç:** İP-B ile ilgili dokümanları (README, KURALLAR, PLAN, architecture, domain-design, api-contract, ADR-008, ADR-009) okumak ve belirsiz yerleri bulmak.
- **Prompt (özet):** "Dokümanları bana tek tek, anlayacağım şekilde açıkla; ilk doküman PR'ım için düzeltilecek bir yer bul."
- **Sonuç:** domain-design.md § 4'teki `to_sections()` metodunun hangi işe ait olduğu netleştirildi. Düzenlemeleri, commit'leri ve PR'ı Özlem'in isteğiyle Claude yaptı; içeriği Özlem onayladı.
- **Yapay zekanın hataları / eksikleri:** Dokümanlarda `to_sections()` PageContent altında yazıyordu ama #6'da yoktu ve ADR-009 bölme işini `chunk_page`'e veriyordu.
- **Bizim müdahalemiz:** Belirsizliği gidermek için metodun #13 (parçalama) ile birlikte yazılacağını belirten bir not eklenmesine karar verdim.
- **Ders çıkarımı:** Görev kartı ile doküman arasında fark varsa kodlamaya başlamadan önce netleştirmek gerekir.
- 
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
