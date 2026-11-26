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
