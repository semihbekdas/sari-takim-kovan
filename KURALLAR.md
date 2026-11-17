# Kovan — Ekip Çalışma Kuralları

> Bu kurallar hocanın proje kriterlerinden ([`course-guide.md`](https://github.com/buraksenyurt/ai-based-development-lecture/blob/main/course-guide.md)) ve derste söylediklerinden türetilmiştir. Amaç: **eşit katkı, tarihsel commit geçmişi, mimariye uyum, testli ve dokümante kod.**
> Yapay zeka ajanları için teknik kurallar ayrıca [`AGENTS.md`](AGENTS.md) dosyasındadır.

---

## 1. Altın kurallar

1. **Commit'ini attığın her satırı anlayabilmelisin.** Kodu yapay zeka yazmış olabilir; sunumda soru sana gelir. Anlamadığın kodu commit'leme.
2. **Her şey zamana yayılır.** Kod son hafta tek seferde gelmez. Küçük adımlar, sık commit.
3. **Herkes eşit katkı verir.** Commit, PR ve review sayıları üyeler arasında dengeli olmalı.
4. **Mimari dokümanda ne yazıyorsa kod odur.** Dokümana uymayan kod ya düzeltilir ya da önce doküman (ADR) güncellenir.
5. **Testi olmayan özellik bitmiş sayılmaz.**

---

## 2. Git ve GitHub

### 2.1 Hesap ayarı (ilk gün, herkes)

Commit'lerin GitHub'da **senin adına** görünmesi için yerel git e-postan GitHub hesabındaki e-posta ile aynı olmalı:

```bash
git config --global user.name  "Ad Soyad"
git config --global user.email "github-hesabindaki@eposta.com"
```

> ⚠️ Bu ayar yanlışsa commit'lerin GitHub'da kimseye ait görünmez ve **katkın sayılmaz**.

### 2.2 Branch akışı

- `main` korumalıdır: doğrudan push yok, sadece PR ile merge.
- Her iş için yeni branch: `feature/<iş-paketi>-<kısa-ad>`, `fix/<kısa-ad>`, `docs/<kısa-ad>`, `test/<kısa-ad>`
  - Örnek: `feature/sayfalar-agac-menu`, `feature/indeks-chunking`, `docs/adr-qdrant`
- Branch ömrü kısa olsun (en fazla ~1 hafta). Uzun yaşayan branch = büyük çakışma.

### 2.3 Commit kuralları

- **Herkes kendi hesabından, kendi işini commit'ler.** Başkasının kodunu senin hesabından push'lamak yok.
- **Küçük ve anlamlı commit:** Bir commit bir mantıksal değişiklik.
- **Hedef tempo:** Herkes haftada **en az 3 commit**, en az **2 farklı günde**.
- **Commit tarihleriyle oynamak yasak** (`--date`, `GIT_COMMITTER_DATE`, rebase ile geçmiş değiştirme vb.). Tarihsel geçmiş, işi gerçekten zamana yayarak oluşur.
- Mesaj formatı ([Conventional Commits](https://www.conventionalcommits.org/)), açıklama Türkçe:

```text
<tür>(<kapsam>): <kısa açıklama>

[isteğe bağlı detay: neden yapıldı]
```

| Tür | Ne zaman |
| --- | --- |
| `feat` | Yeni özellik |
| `fix` | Hata düzeltme |
| `test` | Test ekleme/düzeltme |
| `docs` | Doküman |
| `refactor` | Davranışı değiştirmeyen kod iyileştirmesi |
| `chore` | Bağımlılık, yapılandırma, CI vb. |

Örnekler:
```text
feat(pages): sayfa taşıma uç noktası eklendi
test(chunking): başlık hiyerarşisine göre parçalama kabul testleri (AC-10.1)
fix(search): çöp kutusundaki sayfalar arama sonuçlarından çıkarıldı
docs(adr): ADR-004 Qdrant seçimi gerekçesi yazıldı
```

❌ Kötü örnekler: `update`, `fix`, `son hali`, `asdf`, `çalışıyor artık`

### 2.4 Pull Request kuralları

- Her PR **tek bir iş** içerir; mümkünse **≤ 400 satır** değişiklik.
- PR açıklaması şablonu:

```markdown
## Ne yapıldı?
## Neden? (ilgili kullanıcı hikayesi / kabul kriteri: US-xx, AC-xx.x)
## Nasıl test edildi?
## Yapay zeka kullanımı (hangi araç, önemli prompt, neyi düzelttim)
## Ekran görüntüsü (UI değişikliği varsa)
```

- **En az 1 onay (review)** gerekir; PR'ı açan kişi kendi PR'ını onaylayamaz.
- **CI yeşil olmadan merge yok** (testler + lint + mimari kontrol + Sonar quality gate).
- Merge yöntemi: **"Create a merge commit"** veya **"Rebase and merge"**. **Squash kullanmıyoruz** — squash, herkesin ayrı commit'lerini tek commit'e ezer ve tarihsel geçmişi siler.
- Review yapan kişi kodu gerçekten okur ve en az bir yorum/soru bırakır. "LGTM" tek başına review sayılmaz.

### 2.5 Eşit katkı takibi

Her hafta sonu toplantısında:
```bash
git shortlog -sn --all --no-merges     # kişi başı commit sayısı
```
GitHub → **Insights → Contributors** sayfasına da bakılır. Dengesizlik varsa bir sonraki haftanın iş dağılımı buna göre düzeltilir.

---

## 3. Mimari kuralları (özet)

Ayrıntı: [`docs/architecture.md`](docs/architecture.md), [`docs/adr/`](docs/adr/)

- Backend katmanları: `domain`, `application`, `infrastructure`, `api`. Bağımlılık yönü: `api → application → domain` ve `infrastructure → application / domain`.
- **`domain` hiçbir şeye bağımlı değildir** (FastAPI, SQLAlchemy, Qdrant import edilemez).
- **`application`** iş akışlarını yönetir; veritabanı, Qdrant ve LLM'e sadece **arayüzler (port)** üzerinden erişir.
- **`infrastructure`** bu arayüzleri uygular (PostgreSQL, Qdrant, LLM istemcisi).
- **`api`** sadece HTTP ↔ uygulama servisi çevirisi yapar; iş kuralı içermez.
- Bu kurallar **import-linter** ile CI'da otomatik denetlenir ([mimari-secimi.md § 7](docs/mimari-secimi.md#7-uyumu-nasıl-kanıtlayacağız)).
- Yeni bir teknoloji/kütüphane eklemek veya mimari değiştirmek = **önce ADR** yaz, ekipten onay al.

---

## 4. Kod kuralları

- **Okunabilirlik önce gelir.** Açık isimler, kısa fonksiyonlar (hedef ≤ 30 satır), derin iç içe `if` yok (erken dönüş kullan).
- Python: tip ipuçları zorunlu, `ruff` (lint + format) ve `mypy` temiz olmalı.
- TypeScript: `strict` mod, `eslint` + `prettier` temiz olmalı, `any` yok.
- **Boş `except`/`catch` yasak.** Hata ya ele alınır, ya üst katmana iletilir, ya da loglanır (ders Bölüm 4: *Do Not Swallow Errors*).
- Kod tekrarından kaçın (Sonar duplication < %3).
- Kodda yorum "ne"yi değil **"neden"i** anlatır.
- Kullanılmayan kod, yorum satırına alınmış eski kod commit'lenmez.
- İsimlendirme: kod ve tanımlayıcılar **İngilizce**; doküman, commit açıklaması ve kullanıcıya görünen metinler **Türkçe**.

---

## 5. Test kuralları

Ayrıntı: [`docs/test-strategy.md`](docs/test-strategy.md)

- Her **Must** kabul kriteri (AC) en az bir teste bağlanır; Should işleri yapılırsa onların AC'leri de. Test, AC kimliğini taşır: `@pytest.mark.ac("AC-04.3")`.
- Test türleri: **birim** (domain/application), **entegrasyon** (gerçek PostgreSQL + Qdrant, Testcontainers), **kabul** (API senaryoları); *(Should)* birkaç Playwright duman testi.
- Testler gerçek yapay zeka API'si çağırmaz; fake sağlayıcılar kullanılır.
- Hata yolları da test edilir (geçersiz girdi, yetkisiz erişim, servis kapalı) — *negative path testing*.
- Assert içermeyen test, `skip` ile kapatılmış test, coverage'tan dosya hariç tutma **yasak**. Tek istisna: Docker gerektiren entegrasyon testleri **yerelde** Docker kapalıysa atlanır; **CI'da Docker zorunludur**, yoksa test hata verir.
- Yeni kod, mevcut testleri kırmadan gelir.

---

## 6. Doküman kuralları

- Davranış değiştiren her PR, ilgili dokümanı da günceller (`api-contract.md`, `domain-design.md`, `user-stories.md` …).
- Geri dönülmesi zor her karar → `docs/adr/` altına yeni ADR (ders Bölüm 7).
- `docs/PLAN.md` her hafta sonu toplantısında güncellenir (ilerleme + skor kartı).
- `README.md` her sprint sonunda güncel tutulur.

---

## 7. Yapay zeka kullanım kuralları

- Ajanı başlatmadan önce ilgili dokümanları bağlam olarak ver (`AGENTS.md` bunu otomatik sağlar).
- Büyük bir işi tek prompt'ta yaptırma; **küçük parçalar halinde** ilerle (ders Bölüm 1).
- Üretilen kodu **satır satır oku**, çalıştır, testini gör. "Derleniyor" ≠ "doğru".
- Ajanın `try/except: pass` ile hata gizlemesine, testleri silmesine/atlamasına, gereksiz bağımlılık eklemesine izin verme.
- **Prompt'lara asla** şifre, API anahtarı, `.env` içeriği, kişisel veri yapıştırma (ders README'sindeki "Aman Dikkat" bölümü).
- Önemli prompt'ları, yapay zekanın yaptığı hataları ve senin düzeltmelerini [`docs/ai-log.md`](docs/ai-log.md)'ye yaz. README'deki "Yapay Zeka Kullanımı" ve "Zorluklar" bölümleri buradan beslenir.
- PR açıklamasındaki "Yapay zeka kullanımı" bölümünü doldur.

---

## 8. Güvenlik kuralları

> ⚠️ **Repo public.** Commit'lenen her şeyi herkes görür; silinen bir commit bile geçmişte kalır. Sızan bir API anahtarı dakikalar içinde kötüye kullanılabilir.

- Gizli bilgiler (şifre, API anahtarı, JWT secret) **sadece `.env`** dosyasında; `.env` asla commit'lenmez (`.gitignore`'da), `.env.example` sahte değerlerle commit'lenir.
- GitHub'da **secret scanning ve push protection** açık tutulur.
- **API anahtarları:** Sağlayıcı panelinde ortak bir organizasyon/proje açılır, üç üye davet edilir, **herkes kendi anahtarını** üretir. Anahtar WhatsApp, e-posta veya prompt içinde paylaşılmaz. Panelde **aylık harcama limiti** tanımlanır.
- Günlük geliştirme ve testler **fake** yapay zeka modunda yapılır; gerçek API yalnızca gerektiğinde açılır (maliyet).
- Bir anahtar yanlışlıkla commit'lenirse: hemen sağlayıcı panelinden **iptal edilir**, yenisi üretilir, ekibe haber verilir (geçmişten silmek yetmez).
- Her veritabanı ve Qdrant sorgusu **kullanıcıya göre filtrelenir** (`owner_id`). Başka kullanıcının kaynağı → **404**.
- SQL her zaman parametreli; ham string birleştirme yok.
- Kullanıcı içeriği HTML olarak basılmaz (`dangerouslySetInnerHTML` yasak).
- Sayfa içeriği LLM'e **veri** olarak gider; içindeki talimatlar uygulanmaz (prompt injection önlemi, ders Bölüm 18).
- Bağımlılıklar güncel ve güvenilir kaynaktan; Dependabot uyarıları göz ardı edilmez.

---

## 9. "Bitti" tanımı (Definition of Done)

Bir iş ancak şunların hepsi sağlanınca biter:

- [ ] Kabul kriterleri karşılandı ve her AC'ye bağlı test var
- [ ] Testler, lint, tip kontrolü ve mimari kontrol CI'da yeşil
- [ ] SonarQube Cloud quality gate yeşil (yeni kodda A derecesi, açık kritik bulgu yok)
- [ ] En az 1 ekip arkadaşı review etti
- [ ] İlgili doküman güncellendi
- [ ] Yapay zeka kullanımı PR açıklamasına / ai-log'a yazıldı
- [ ] Commit'i atan kişi kodu anlatabiliyor

---

## 10. Haftalık rutin

| Ne zaman | Ne |
| --- | --- |
| **Hafta içi** | Küçük commit'ler, PR'lar, review'lar; takıldığın yeri ekip grubuna yaz |
| **Hafta sonu toplantısı** (Cumartesi veya Pazar, ~45 dk) | 1) Geçen sprintin demosu: herkes kendi işini 5 dk gösterir · 2) **Kriter skor kartı** puanlaması ve `git shortlog` ile katkı kontrolü · 3) Yeni sprintin işleri ve sahipleri · 4) Hocaya sorulacak sorular · 5) `PLAN.md` güncellemesi |

---

## 11. Sunum kuralı

Sunum en fazla **25 dakika**. Herkes **kendi iş paketini ve kodunu** anlatır; her üye, diğer iki üyenin modülü hakkında da temel sorulara cevap verebilecek kadar bilgi sahibi olur (review'lar bunu sağlar).
