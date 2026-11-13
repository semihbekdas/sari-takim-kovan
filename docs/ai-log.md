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
> - Her üye, Sprint 0'da kendi commit'leyeceği dokümanları okuyunca bu alana bir satır ekler.

### 2026-11-13 — Ders reposunun analizi ve proje dokümanlarının taslağı
- **Kim:** ✍️ DOLDURULACAK *(oturumu yürüten üye)*
- **Araç / model:** Claude Code (Claude Opus 5.5)
- **Amaç:** Ders reposundaki (`buraksenyurt/ai-based-development-lecture`) proje kriterlerini, örnek projeleri (lesson01, lesson05 ADR'leri, ProjectRouter, lesson07/08 RAG örnekleri) incelemek; P0007 için mimari, plan, kurallar, kullanıcı hikayeleri ve ADR taslaklarını oluşturmak.
- **Prompt (özet):** "Notion ile başlayalım, dokümanları hazırla; önce hocanın reposundaki proje ile ilgili kısımları detaylıca incele, sonra hangi mimariyi neden kullandığımızı, planımızı, README'yi oluştur; ayrıca uygulama özelliklerini ve kuralları ayrı dosyalara yaz."
- **Sonuç:** `README.md`, `OZELLIKLER.md`, `KURALLAR.md`, `AGENTS.md`, `CLAUDE.md`, `docs/*` ve `docs/adr/ADR-001…010` taslakları.
- **Yapay zekanın hataları / eksikleri:** Bu taslağın hataları aynı gün yapılan revizyonda bulundu, bkz. bir sonraki kayıt. Sizin bulduklarınızı da buraya ekleyin.
- **Bizim müdahalemiz:** ✍️ DOLDURULACAK *(her üye kendi commit'lediği dokümanı okuyunca yaptığı değişikliği yazar)*
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
