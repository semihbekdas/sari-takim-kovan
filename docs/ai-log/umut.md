# Yapay Zeka Kullanım Günlüğü — Umut

> Umut'un (İP-A) kayıtları. Şablon ve kurallar: [README.md](README.md). Kayıtlar tarih sırasıyla, en yenisi en altta.

### 2026-11-20 — Umut: doküman okuma (#2)
- **Kim:** Umut
- **Araç / model:** Claude (claude.ai)
- **Amaç:** İP-A ile ilgili dokümanları (README, KURALLAR, PLAN, architecture, domain-design, ADR-003, ADR-004, ADR-007) okumak ve kendi işlerim (#3 docker-compose + Alembic, #4 frontend iskeleti) öncesi eksikleri görmek.
- **Prompt (özet):** "Bana atanan issue'ları ve ilgili dokümanları anlat; ilk doküman PR'ım için adım adım yardım et."
- **Sonuç:** İP-A kapsamı ve Sprint 1–2 işlerim netleşti. Dokümanlarda Alembic ve qdrant-client kullanılacağı yazıyor ama `backend/pyproject.toml`'da henüz bağımlılık olarak yoklar; Alembic #3'te, qdrant-client #14'te eklenecek.
- **Yapay zekanın hataları / eksikleri:** Önemli bir hata görmedim.
- **Bizim müdahalemiz:** Okundu, doküman değişikliği yok. Eksik bağımlılıkları #3'ün yapılacaklar listesine aldım.
- **Ders çıkarımı:** Kodlamaya başlamadan önce dokümanla repodaki mevcut durumu karşılaştırmak, hangi işin bende olduğunu netleştiriyor.

### 2026-11-20 — Umut: docker-compose ve Alembic (#3, PR #23)
- **Kim:** Umut
- **Araç / model:** Claude (claude.ai)
- **Amaç:** PostgreSQL + Qdrant için `docker-compose.yml`, Alembic kurulumu ve migration testlerini hazırlamak; Docker, WSL ve uv'yi ilk kez kurmak.
- **Prompt (özet):** "#3'ü adım adım yapalım; Docker ve Git'i ilk kez kullanıyorum."
- **Sonuç:** `docker-compose.yml` (kalıcı volume, healthcheck, portlar yalnızca 127.0.0.1), `backend/alembic.ini`, `backend/migrations/`, `tables.py` (naming convention), `tests/conftest.py`'de ortak `postgres_url` / `db_engine` fixture'ı, `test_migrations.py`. 65 test kendi bilgisayarımda Docker ile geçti, `/api/v1/health/ready` 200 döndü.
- **Yapay zekanın hataları / eksikleri:** İlk sürüm issue'daki maddelerin bir kısmını kaçırdı: Qdrant sürümü v1.20.2 yerine v1.20.0'dı, Qdrant'ta healthcheck yoktu, ortak fixture `conftest.py` yerine tek test dosyasındaydı. Kurulumda Docker'ın WSL gerektirdiğini önceden söylemedi; hatayı görünce çözüm adımlarını verdi.
- **Bizim müdahalemiz:** Takım arkadaşımın issue listesiyle yaptığı kontrol bu üç eksiği buldu; ertesi gün düzeltip ayrı commit'ler attım. Semih'in review'undaki "her test temiz veriyle başlasın" önerisini #9'a aldım.
- **Ders çıkarımı:** Yapay zekanın çıktısını PR'dan önce issue'daki "bitti tanımı" maddeleriyle tek tek karşılaştırmak gerekiyor.

### 2026-11-21 — Umut: frontend iskeleti (#4, PR #24)
- **Kim:** Umut
- **Araç / model:** Claude (claude.ai)
- **Amaç:** Vite + React + TypeScript (strict), React Router, TanStack Query; ana yerleşim, tipli API istemcisi, Vite proxy, eslint/prettier ve Vitest.
- **Prompt (özet):** "#4'ü adım adım yapalım."
- **Sonuç:** `frontend/` iskeleti; `src/api/client.ts` hata formatını tek `ApiError` tipine çeviriyor; 10 Vitest testi. Backend açıkken sol menüde "Sunucu: bağlı" göründü (istek Vite proxy'si üzerinden gitti).
- **Yapay zekanın hataları / eksikleri:** API istemcisinde `credentials: "include"` kullandı; Vite proxy ile istekler aynı origin'den gittiği için `"same-origin"` daha güvenli (Semih'in review'u). Sonar'ın PR'da %0 kapsam vermesinin sebebini bulamadı; sebep Sonar ayarıymış, Semih #25'te düzeltti.
- **Bizim müdahalemiz:** Uygulamayı backend kapalıyken ve açıkken elle denedim. `same-origin` düzeltmesi #10'da yapılacak.
- **Ders çıkarımı:** Kalite kapısı düşünce önce kendi kodumu değil, analizin neyi ölçtüğünü kontrol etmek gerekiyor.

### 2026-11-25 — Umut: sayfa domain'i (#9, 1/3, PR #31)
- **Kim:** Umut
- **Araç / model:** Claude (claude.ai)
- **Amaç:** `pages` tablosu `users`'a (#11) bağlı olduğu için #9'u 3 PR'a bölmek; ilk PR'da veritabanından bağımsız `Page` aggregate'ini yazmak.
- **Prompt (özet):** "#9'u yapalım; her adımı neden yaptığımızla birlikte anlat."
- **Sonuç:** `domain/pages.py`: R-03 başlık (boş → "Adsız", > 200 → 422 `TITLE_TOO_LONG`), R-07 sürüm çakışması (409 `VERSION_CONFLICT`), R-10/R-11 kayıtta sürüm artışı ve indeks sayacının sıfırlanması, `index_status`. 18 birim testi, kapsam %100. `api-contract.md`'ye `TITLE_TOO_LONG` eklendi.
- **Yapay zekanın hataları / eksikleri:** İlk açıklaması fazla hızlı ve teknikti; neyin neden yapıldığını adım adım anlatmasını istedim.
- **Bizim müdahalemiz:** Testleri ve CI kontrollerini (ruff, mypy, lint-imports, pytest) kendi bilgisayarımda çalıştırıp sonuçları okudum; PR'ı "Closes" değil "Part of #9" ile açtım ki #9 erken kapanmasın.
- **Ders çıkarımı:** Bağımlılığı olan büyük bir işi, bağımlılık gerektirmeyen parçadan başlayarak bölmek beklerken de ilerlemeyi sağlıyor.

### 2026-11-26 — Umut: pages tablosu ve repository (#9, 2/3)
- **Kim:** Umut
- **Araç / model:** Claude (claude.ai)
- **Amaç:** `pages` tablosunu Özlem'in `users` tablosunun (#34) üstüne kurmak; sayfaları veritabanına yazan/okuyan repository'yi ve Semih'in #23'te önerdiği "her test geri alınan işlem içinde" fixture'ını eklemek.
- **Prompt (özet):** "#9'un 2. parçasını hazırla; #34 merge olmadan da ilerleyebilelim."
- **Sonuç:** `tables.py`'de `pages` (domain-design § 9: FK'ler `ON DELETE CASCADE`, iki kısmi indeks), Alembic migration'ı, `SqlPageRepository` (`add`, `get`, `update`; `update` sürüm kontrolünü `UPDATE … WHERE version = :beklenen` ile tek adımda yapıyor, R-07), `db_connection` fixture'ı, 9 entegrasyon testi (sahiplik R-04, silinmiş sayfa R-08, sürüm çakışması R-07, bilinmeyen kullanıcı FK hatası).
- **Yapay zekanın hataları / eksikleri:** İlk taslakta `PageRepository` port'unu da ekledi; ama port'u kullanan servis henüz yok ("kullanılmayan kod commit'lenmez") ve aynı satırı Semih'in #30'u da değiştiriyordu. Port 3. parçaya, servisle birlikte bırakıldı. Ayrıca Özlem'in dalının #31'den önceki `main`'e dayandığını ilk denemede atladı (import hatası); dala `main` merge edilerek çözüldü.
- **Bizim müdahalemiz:** Testleri kendi bilgisayarımda Docker ile çalıştırdım; PR'ı #34'e bağlı olduğunu belirterek açtım.
- **Ders çıkarımı:** Başkasının dalının üstüne çalışırken önce o dalın hangi `main`'e dayandığına bakmak gerekiyor.

### 2026-11-27 — Umut: sayfa oluşturma ve görüntüleme API'si (#9, 3/4)
- **Kim:** Umut
- **Araç / model:** Claude (claude.ai)
- **Amaç:** Özlem'in giriş PR'ı (#38) gelince `POST /pages` ve `GET /pages/{id}`'yi `CurrentUser` üzerine kurmak; breadcrumb'ı (AC-05.2) eklemek.
- **Prompt (özet):** "#9'un API kısmını hazırla; her adımı neden yaptığımızla anlat."
- **Sonuç:** `PageRepository` ve `PageTransactions` port'ları, `PageService` (R-04: başkasının sayfası ve başkasının üst sayfası 404), istek başına tek veritabanı işlemi (`SqlPageTransactions`), breadcrumb için özyinelemeli sorgu (recursive CTE), 7 kabul + 2 entegrasyon testi.
- **Yapay zekanın hataları / eksikleri:** İlk taslak `PUT`'u da içeriyordu ve 495 satırdı (sınır 400); kaydetme 4. parçaya ayrıldı. Ayrıca önce kodu henüz PR'ı olmayan ve `main` ile çakışan giriş dalının üstüne kurmayı önerdi; Özlem'e PR'ı ne zaman açacağını GitHub'da sorup #38'i bekledik.
- **Bizim müdahalemiz:** #37 ve #38'i Claude ile birlikte inceledim; #37'de Sonar'ı düşüren aynı ifade karşılaştırmasını (S1764) Özlem'e yazdım. Testleri kendi bilgisayarımda Docker ile çalıştırdım.
- **Ders çıkarımı:** PR'ı baştan uç nokta bazında küçük planlamak, sonradan bölmekten kolay.

### 2026-11-27 — Umut: sayfa kaydetme API'si (#9, 4/4)
- **Kim:** Umut
- **Araç / model:** Claude (claude.ai)
- **Amaç:** 3. parçadan 400 satır sınırı yüzünden ayrılan `PUT /pages/{id}`'yi eklemek.
- **Prompt (özet):** "#9'un son parçasını hazırla."
- **Sonuç:** `PageService.update`: R-06 içerik kontrolü, R-07 sürüm kontrolü (eski sürümle 409, içerik ezilmez), kayıtta sürüm artar ve indeks durumu PENDING olur (AC-04.5). 4 kabul testi (AC-04.3, AC-04.4, AC-04.5, başka kullanıcı 404).
- **Yapay zekanın hataları / eksikleri:** Kodu ayırırken 3. parçada kısalttığı açıklama satırları bu parçada eski uzun hallerine geri geldi; fark edip düzeltti.
- **Bizim müdahalemiz:** 409 testinin "ikinci sekme" senaryosunu (aynı sürümle iki kayıt) okuyup gerçek kullanımla karşılaştırdım; testleri kendi bilgisayarımda çalıştırdım.
- **Ders çıkarımı:** Küçük PR'lar review'u da hızlandırıyor: 3. parça birkaç dakikada onaylandı.

### 2026-11-28 — Umut: sayfa ağacı (#9, 5/5)
- **Kim:** Umut
- **Araç / model:** Claude (claude.ai)
- **Amaç:** #9'un son maddesi `GET /pages/tree`: sol menü için kullanıcının silinmemiş sayfaları, `has_children` ve kardeşlerin Türkçe alfabetik sırası (AC-05.1).
- **Prompt (özet):** "#9'da başka ne kaldı? Ağacı hazırla."
- **Sonuç:** `PageRepository.tree` (`ORDER BY title COLLATE "tr-x-icu"`, alt sayfa kontrolü `EXISTS` ile, en fazla 1000 sayfa), `PageService.tree`, `/pages/tree` uç noktası (`/{page_id}`'den önce tanımlı). 2 entegrasyon + 1 kabul testi; 401 testine ağaç da eklendi.
- **Yapay zekanın hataları / eksikleri:** 4. parçayı "4/4" diye adlandırdı; issue'daki listeyi kontrol etmeden #9'un bittiğini varsaymıştı. Issue'yu birlikte okuyunca ağacın eksik olduğu çıktı.
- **Bizim müdahalemiz:** #9'u açıp yapılacaklar listesini PR'larla karşılaştırdım; Türkçe sıralamanın (Cam < Çay < Işık < İz) testte gerçekten denendiğini kontrol ettim; testleri kendi bilgisayarımda çalıştırdım.
- **Ders çıkarımı:** "Bitti" demeden önce issue'daki "Bitti sayılır" listesine madde madde bakmak gerekiyor.

### 2026-11-28 — Umut: değerlendirme seti sayfaları ve soruları (#17)
- **Kim:** Umut
- **Araç / model:** Claude (claude.ai)
- **Amaç:** Ortak RAG değerlendirme setine (`eval/`, #29) kendi 5 kurgusal sayfamı ve 7 sorumu eklemek.
- **Prompt (özet):** "Alanıma yakın, gerçek kişisel bilgi içermeyen 5 konu öner; sayfaları ve soruları taslak olarak hazırla."
- **Sonuç:** `eval/dataset/umut/`: ESP32 sıcaklık projesi, Thevenin/Norton, op-amp devreleri, güneş paneli kurulumu ve kurgusal bir firmada staj notları. `eval/questions/umut.toml`: 3 normal, 2 eş anlamlı, 1 talimat sızdırma (staj sayfasına gizlendi), 1 "bulunamadı" (asenkron motor; hiçbir sayfada geçmiyor, kontrol edildi). `--provider fake` ile betik hatasız çalıştı; her bölüm 350 karakterin altında (sınır 1000).
- **Yapay zekanın hataları / eksikleri:** Sayfaları yapay zeka taslak olarak yazdı; konu seçimi ve teknik doğruluk benim kontrolümde. Sahte (fake) sağlayıcıyla eş anlamlı sorular bulunamadı; bu beklenen bir durum (sahte model kelime benzerliğine bakıyor), gerçek ölçüm Semih'in betiğiyle yapılacak.
- **Bizim müdahalemiz:** Konuları alanımdan (EEM) seçtim; formülleri (Av = −Rf/Rin, Pmax = Vth²/4Rth, RL = Rth) derslerimden kontrol ettim; eş anlamlı soruların sayfadaki kelimelerden gerçekten farklı olduğuna baktım.
- **Ders çıkarımı:** "Bulunamadı" sorusunun konusu başka üyelerin sayfalarında da geçmemeli; tüm sete aranarak seçildi.
