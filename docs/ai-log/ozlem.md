# Yapay Zeka Kullanım Günlüğü — Özlem

> Özlem'in (İP-B) kayıtları. Şablon ve kurallar: [README.md](README.md). Kayıtlar tarih sırasıyla, en yenisi en altta.

### 2026-11-17 — Özlem: doküman okuma (#5)
- **Kim:** Özlem
- **Araç / model:** Claude (claude.ai, Claude Code)
- **Amaç:** İP-B ile ilgili dokümanları (README, KURALLAR, PLAN, architecture, domain-design, api-contract, ADR-008, ADR-009) okumak ve belirsiz yerleri bulmak.
- **Prompt (özet):** "Dokümanları bana tek tek, anlayacağım şekilde açıkla; ilk doküman PR'ım için düzeltilecek bir yer bul."
- **Sonuç:** domain-design.md § 4'teki `to_sections()` metodunun hangi işe ait olduğu netleştirildi. Düzenlemeleri, commit'leri ve PR'ı Özlem'in isteğiyle Claude yaptı; içeriği Özlem onayladı.
- **Yapay zekanın hataları / eksikleri:** Dokümanlarda `to_sections()` PageContent altında yazıyordu ama #6'da yoktu ve ADR-009 bölme işini `chunk_page`'e veriyordu.
- **Bizim müdahalemiz:** Belirsizliği gidermek için metodun #13 (parçalama) ile birlikte yazılacağını belirten bir not eklenmesine karar verdim.
- **Ders çıkarımı:** Görev kartı ile doküman arasında fark varsa kodlamaya başlamadan önce netleştirmek gerekir.

### 2026-11-20 — Özlem: PageContent içerik doğrulama (#6)
- **Kim:** Özlem
- **Araç / model:** Claude Code
- **Amaç:** `domain/content.py`: R-06 içerik doğrulaması, `to_plain_text()` ve `mentioned_page_ids()`; birim testleri.
- **Prompt (özet):** "Issue #6'yı küçük parçalara böl, her parçanın kodunu ve testini adım adım birlikte yazalım."
- **Sonuç:** PR #21. İş küçük commit'lere bölündü; testler her adımda yerelde çalıştırıldı.
- **Yapay zekanın hataları / eksikleri:** İlk taslakta dosya sonu satırı eksikti (`ruff`). Bozuk şekilli girdi (ör. `props: null`) 500 veriyordu, link içeriği kontrol edilmiyordu, çok derin iç içe blok `RecursionError` veriyordu. "İzin verilir" testlerinde assert yoktu. Davranışlar sınıf yerine ayrı fonksiyonlardı.
- **Bizim müdahalemiz:** `ruff format`'ı her commit öncesi çalıştırmayı alışkanlık yaptım. Review'da Umut ve Semih'in bulduklarını düzelttim: şekil kontrolü, link içeriği, iç içe sınırı (20, R-06'ya eklendi), assert'li testler ve `PageContent` değer nesnesi.
- **Ders çıkarımı:** Bozuk girdi ve uç durumları ayrıca denemek gerekiyor. Görev kartındaki tasarımı (değer nesnesi) baştan izlemek sonradan yeniden yazmayı önlüyor.

### 2026-11-23 — Özlem: users tablosu ve migration'ı (#11)
- **Kim:** Özlem
- **Araç / model:** Claude Code
- **Amaç:** `users` tablosu (domain-design § 9), `lower(email)` üzerinde benzersiz indeks (R-01) ve ilk Alembic migration'ı.
- **Prompt (özet):** "#11'i iki PR'a böl; önce `users` tablosunu, migration'ını ve tablo testlerini hazırla."
- **Sonuç:** `infrastructure/db/tables.py`, migration `08ffb3ff6603`, `tests/integration/test_users_table.py`. #9 ve #12 bu tabloya bağlı olduğu için ayrı PR yapıldı.
- **Yapay zekanın hataları / eksikleri:** Autogenerate fonksiyon tabanlı indeksi (`lower(email)`) üretmedi; migration'a elle eklendi. Tablo testleri önce kendi temizleme fixture'ını kullanıyordu, register testleri gelince ortak `conftest.py`'ye taşındı.
- **Bizim müdahalemiz:** İşi iki PR'a bölmeye ben karar verdim: önce users tablosu, sonra kayıt uç noktası. Migration'daki lower(email) benzersiz indeksini ve testleri kontrol ettim, büyük/küçük harf farklı aynı e-postanın reddedildiğini doğruladım.
- **Ders çıkarımı:** Autogenerate çıktısı her zaman gözden geçirilmeli; `tables.py` ↔ migration uyumu testi bunu yakalıyor.

### 2026-11-24 — Özlem: kayıt olma uç noktası (#11)
- **Kim:** Özlem
- **Araç / model:** Claude Code
- **Amaç:** `POST /auth/register`: R-01 e-posta kontrolü, R-02 şifre uzunluğu, Argon2id ile hash (ADR-008), 409 `EMAIL_TAKEN`; AC-01.1–01.4 testleri.
- **Prompt (özet):** "#11'in ikinci kısmını katmanlara göre küçük commit'lerle yaz: domain → servis → altyapı → API."
- **Sonuç:** `domain/users.py`, `application/auth_service.py`, `application/ports/users.py`, `infrastructure/security/argon2.py`, `infrastructure/db/users.py`, `api/routers/auth.py`; birim, entegrasyon ve kabul testleri. `argon2-cffi` bağımlılığı eklendi (ADR-008).
- **Yapay zekanın hataları / eksikleri:** Serviste görünen ad `strip()` ediliyordu; şemadaki 2–50 kontrolünden sonra ad 1 karaktere düşebilirdi, kaldırıldı. Repository her `IntegrityError`'ı "e-posta kayıtlı" sayabilirdi; yalnızca `ux_users_email` ihlalinin 409 olması sağlandı ve testi eklendi.
- **Bizim müdahalemiz:** Kodu katmanlara göre küçük commit'lerle ilerletmeye ben karar verdim. Testleri çalıştırıp büyük harfli e-postayla kayıt olunca 409 döndüğünü ve şifrenin veritabanında Argon2 hash olarak durduğunu kontrol ettim.
- **Ders çıkarımı:** Aynı kural iki katmanda (şema ve servis) farklı uygulanırsa tutarsızlık çıkıyor; kuralın tek yeri olmalı.

### 2026-11-26 — Özlem: giriş, çıkış ve `/auth/me` (#12)
- **Kim:** Özlem
- **Araç / model:** Claude Code
- **Amaç:** `POST /auth/login`, `POST /auth/logout`, `GET /auth/me` ve korumalı uç noktalar için `current_user` bağımlılığı (US-02, ADR-008); AC-02.1–02.4 testleri.
- **Prompt (özet):** "#12'yi kayıt dalının üstüne kur; katmanlara göre küçük commit'lerle yaz, JWT çerez yaklaşımı ADR-008'e uysun."
- **Sonuç:** `infrastructure/security/jwt.py` (HS256, `sub = user_id`, 8 saat), `AuthService.login` / `current_user`, `api/deps.py`'de `CurrentUser`, `kovan_session` çerezi (`HttpOnly; SameSite=Strict; Path=/api`, ayarla `Secure`). `JWT_SECRET` boşsa veya 32 karakterden kısaysa uygulama açılmıyor. `pyjwt` bağımlılığı eklendi (karar: Özlem).
- **Yapay zekanın hataları / eksikleri:** `JWT_SECRET` zorunlu olunca ayarları elle kuran bir test (`test_ai_factory`) kırıldı, düzeltildi. Servis ilk taslakta token hatasını gereksiz yere ikinci kez sarıyordu, sadeleştirildi.
- **Bizim müdahalemiz:** JWT için PyJWT kütüphanesini kullanmaya ben karar verdim. Yanlış e-posta ve yanlış şifrede aynı hata mesajının döndüğünü ve çerezin 8 saat geçerli olduğunu kontrol ettim.
- **Ders çıkarımı:** Kayıtsız e-postada da şifre hash'i doğrulanmalı; yoksa yanıt süresinden e-postanın kayıtlı olup olmadığı anlaşılabilir.

### 2026-11-26 — Özlem: içerik doğrulamada tür kontrolü (#13)
- **Kim:** Özlem
- **Araç / model:** Claude Code
- **Amaç:** Semih'in PR #21 review notu: blok/satır içi `type` veya başlık `level`'ı liste ya da nesne gelirse `in frozenset` kontrolü `TypeError` verip 500 dönüyordu.
- **Prompt (özet):** "Semih'in #21 notunu düzelt: isinstance kontrolü ve testler."
- **Sonuç:** `domain/content.py`'ye `_is_one_of` yardımcı fonksiyonu; üç kontrol (blok türü, satır içi tür, başlık seviyesi) bunu kullanıyor. 5 yeni test, düzeltmeden önce hepsi düşüyordu.
- **Yapay zekanın hataları / eksikleri:** #21'deki ilk sürümde değerin tipine bakılmadan `in` kullanılmıştı. Test yazarken ek bir hata çıktı: Python'da `True == 1` olduğu için `level: true` geçerli başlık sayılıyordu; o da düzeltildi.
- **Bizim müdahalemiz:** Semih'in review notunu takip ettim; level: true hatasını testte görünce onun da düzeltilmesini istedim.
- **Ders çıkarımı:** JSON'dan gelen her alanın tipi, kullanılmadan önce kontrol edilmeli; `bool`'un `int` sayılması gibi Python özellikleri test edilmeli.

### 2026-11-27 — Özlem: başlığa göre parçalama (#13)
- **Kim:** Özlem
- **Araç / model:** Claude Code
- **Amaç:** `PageContent.to_sections()` ve `application/chunking.py` içinde `chunk_page(title, content)` (ADR-009); `CHUNK_MAX_CHARS` ayarı (varsayılan 1000).
- **Prompt (özet):** "#13'ün asıl parçalama modülünü ADR-009'a göre yaz: başlık bölümleri, 1000 karakter sınırı, uzun blok bölme; birim testleriyle küçük commit'ler."
- **Sonuç:** Bölümleme domain'de (`to_sections`), parçalara doldurma application'da (`chunk_page`). Başlıksız sayfa, boş sayfa, çok uzun blok ve Türkçe karakter testleri eklendi.
- **Yapay zekanın hataları / eksikleri:** Şimdilik bulunmadı; review'da çıkarsa eklenecek.
- **Bizim müdahalemiz:** Başlıksız içeriğin sayfa başlığı altında tek bölüm olduğunu ve yalnız başlıktan oluşan bölümün parça üretmediğini testlerde kontrol ettim.
- **Ders çıkarımı:** Bölümlemeyi (ne nereye ait) ve boyut sınırını (ne kadar büyük) ayırmak, iki kuralı ayrı ayrı test etmeyi kolaylaştırdı.

### 2026-11-27 — Özlem: değerlendirme seti payım (#17)
- **Kim:** Özlem
- **Araç / model:** Claude Code
- **Amaç:** Ortak RAG değerlendirme setine (eval/README.md) 5 kurgusal not sayfası ve 7 soru eklemek: 3 normal, 2 eşanlamlı, 1 "notlarda yok", 1 prompt injection.
- **Prompt (özet):** "Seçtiğim 5 konuda (İstanbul'daki tarihi yerler, Türkiye ekonomisi, üniversite eğitim sistemi, İngilizce öğrenme yöntemleri, toplu taşımanın faydaları) sayfalar ve bunlara uygun 7 soru hazırla; her bölüm 1000 karakterden kısa olsun."
- **Sonuç:** `eval/dataset/ozlem/` altında 5 sayfa (her biri 8–9 bölüm, yaklaşık 2.300 karakter), `eval/questions/ozlem.toml` içinde 7 soru. En uzun bölüm 365 karakter (ADR-009 sınırının altında). Betik `--provider fake` ile hatasız çalışıyor.
- **Yapay zekanın hataları / eksikleri:** İlk taslak "ben" diliyle kişisel not gibi yazılmıştı ve sayfalar çok kısaydı; nesnel dile çevrildi ve uzatıldı. "Biraz kısalar" isteği önce yanlış anlaşılıp sayfalar daha da kısaltılmıştı. Ekonomi sayfasında güncel gerçek rakam yanıltıcı olabileceği için rakamlar ders örneği olarak işaretlendi.
- **Bizim müdahalemiz:** Konuları ben seçtim. İlk taslak 'ben' diliyle ve kısa yazılmıştı; nesnel dile çevrilmesini ve sayfaların uzatılmasını istedim. Son metni okuyup onayladım.
- **Ders çıkarımı:** Soruların cevabı yalnızca notlarda olan, sayfaya özgü ayrıntılara (kişisel rakamlar, gün ve saatler) dayanmalı; yoksa model genel bilgisiyle cevap verip aramayı ölçmemizi bozar.
