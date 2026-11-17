# Kovan — Uygulama Özellikleri

> **Kovan**, Notion benzeri bir kişisel bilgi tabanıdır. Sayfalar oluşturup düzenlersin, sayfaları birbirine bağlarsın ve en önemlisi **sayfalarında anlamına göre arama yapar, sayfalarına soru sorarsın** (RAG).
>
> **Sarı Takım** · Ders: Yapay Zeka Destekli Yazılım Geliştirme · Proje kodu: **P0007 – Bilgi Tabanı (Notion Clone + Anlamsal Arama)**
> **Teslim: 25 Aralık 2026** · **Kod dondurma (hedef bitiş): 13 Aralık 2026**
> Bu dosya ekibin "ne yapıyoruz?" sorusuna tek bakışta cevap vermesi için yazıldı. Teknik detaylar `docs/` altındadır.

---

## 0. Neden "Kovan"?

- **Arılar** binlerce çiçekten topladıklarını kovanda **düzenli peteklere** yerleştirir. Kovan da dağınık notları düzenli **sayfalara** toplar.
- Kovandaki **işçi arılar** arka planda sürekli çalışır. Kovan'da da arka planda çalışan bir **indeksleme işçisi** sayfaları yapay zekanın anlayacağı hale getirir. Mimarideki bu bileşenin adı bile isme uyuyor.
- Kısa, Türkçe, akılda kalıcı, telaffuzu kolay; repo adı olarak da sorunsuz (`kovan`, ASCII).
- "Notion" gibi başka bir ürünün marka adını kullanmıyoruz; klon olduğumuzu dokümanda söylüyoruz ama kendi adımız var.

İsim kesinleşti: Repo `sari-takim-kovan`, Python paketi `kovan`.

## 1. Tek cümlede

Kullanıcı notlarını sayfa sayfa yazar. Kovan bu sayfaları arka planda yapay zeka ile indeksler ve kullanıcı *"Veritabanı dersinde normalizasyon hakkında ne yazmıştım?"* diye sorduğunda cevabı **hangi sayfadan aldığını göstererek** verir.

## 2. Örnek kullanım senaryosu

1. Ayşe kayıt olur, giriş yapar.
2. Sol menüden **"Dersler"** adında bir sayfa açar, altına **"Veritabanı"** ve **"Yapay Zeka"** alt sayfalarını ekler.
3. "Veritabanı" sayfasına başlıklar, maddeler, kod blokları içeren notlarını yazar. Yazdıkça **otomatik kaydedilir**.
4. Notun içinde `@Yapay Zeka` yazarak diğer sayfaya **bağlantı** verir. "Yapay Zeka" sayfasının altında *"Bu sayfaya bağlantı verenler: Veritabanı"* görünür.
5. Arama kutusuna *"tabloları bölme kuralları"* yazar. Sayfada bu kelimeler geçmese de **anlamca en yakın** "Normalizasyon" bölümü bulunur.
6. **"Sayfalarına Sor"** ekranında *"3NF ile BCNF farkı ne demiştim?"* diye sorar. Kovan, Ayşe'nin kendi notlarından bir cevap üretir ve altında **[1] Veritabanı › Normalizasyon** şeklinde tıklanabilir kaynak gösterir.
7. Notlarda olmayan bir şey sorarsa uydurmaz: *"Sayfalarında bu konuda bilgi bulamadım."*

---

## 3. Özellik listesi

Öncelikler **MoSCoW** yöntemine göre:
**🟥 Must** (teslimde kesin olacak) · **🟧 Should** (planlandı, Must'lar bitince) · **🟨 Could** (zaman kalırsa) · **⬜ Won't** (bu dönem yok).

### 3.1 Hesap ve güvenlik

| # | Özellik | Öncelik |
| --- | --- | --- |
| F-01 | E-posta + şifre ile **kayıt olma** | 🟥 Must |
| F-02 | **Giriş / çıkış**; oturum güvenli çerezde (httpOnly) | 🟥 Must |
| F-03 | Her kullanıcı **sadece kendi sayfalarını** görür, arar ve sorar | 🟥 Must |
| F-04 | Çok sayıda hatalı girişte geçici engelleme (rate limit) | 🟧 Should |

### 3.2 Sayfalar ve editör

| # | Özellik | Öncelik |
| --- | --- | --- |
| F-05 | Sayfa **oluşturma, görüntüleme, düzenleme** | 🟥 Must |
| F-06 | **Blok tabanlı editör** (Notion tarzı): başlık (H1–H3), paragraf, madde/numaralı liste, yapılacaklar listesi, kod bloğu, alıntı; `/` menüsü, sürükle-bırak ile blok taşıma | 🟥 Must |
| F-07 | **Otomatik kaydetme** (yazmayı bırakınca ~1 sn sonra), "Kaydedildi" göstergesi | 🟥 Must |
| F-08 | İki sekmede aynı sayfa düzenlenirse **veri kaybını önleme** (çakışma uyarısı) | 🟥 Must |
| F-09 | **Alt sayfalar**: sol menüde açılır-kapanır sayfa ağacı, üstte "Dersler › Veritabanı" yolu (breadcrumb) | 🟥 Must |
| F-10 | Sayfa **silme**: sayfa ve alt sayfaları her yerden kaybolur (onay penceresiyle) | 🟥 Must |
| F-11 | Sayfayı başka bir sayfanın altına **taşıma** | 🟧 Should |
| F-12 | **Çöp kutusu ekranı**: silinenleri listeleme, **geri alma**, **kalıcı silme** | 🟧 Should |
| F-13 | **Son düzenlenen sayfalar** listesi (ana ekran) | 🟧 Should |
| F-14 | Sayfayı **Markdown olarak dışa aktarma** | 🟨 Could |

> **Not (F-10 / F-12):** Silinen sayfa veritabanında "silindi" olarak işaretlenir (yumuşak silme). Çöp kutusu **ekranı** Should olsa da bu işaretleme Must'ta yapılır, çünkü yapay zeka indeksinden temizlemeyi basitleştirir (ADR-005) ve çöp kutusu sonradan eklendiğinde veri modeli değişmez.

### 3.3 Sayfalar arası bağlantı

| # | Özellik | Öncelik |
| --- | --- | --- |
| F-15 | Editörde `@` yazınca sayfa seçip **bağlantı** ekleme, tıklayınca o sayfaya gitme | 🟥 Must |
| F-16 | **Geri bağlantılar** (backlinks): "Bu sayfaya bağlantı verenler" paneli | 🟥 Must |
| F-17 | Silinmiş sayfaya giden bağlantının "silinmiş sayfa" olarak gösterilmesi | 🟥 Must |

### 3.4 Arama ve yapay zeka (projenin kalbi)

| # | Özellik | Öncelik |
| --- | --- | --- |
| F-18 | **Kelime araması**: başlık ve içerikte geçen kelimeyi bulma, sonuçta özet | 🟥 Must |
| F-19 | **Anlamsal arama**: kelimeler birebir geçmese de anlamca yakın içerikleri bulma (embedding + Qdrant) | 🟥 Must |
| F-20 | **Arka planda indeksleme**: Sayfa düzenlemesi bitince otomatik olarak yapay zeka indeksine işlenir; sayfada "İndeksleniyor / Güncel / Hata" durumu görünür | 🟥 Must |
| F-21 | **"Sayfalarına Sor" sohbeti** (RAG): soruya kullanıcının kendi notlarından cevap ve **tıklanabilir kaynak** | 🟥 Must |
| F-22 | Notlarda bilgi yoksa **uydurmama**: "bulamadım" cevabı | 🟥 Must |
| F-23 | Yapay zeka servisi kapalıysa çökmeme: anlaşılır hata mesajı, indekslemenin sonra yeniden denenmesi | 🟥 Must |
| F-24 | Yapay zeka **token kullanımının** loglanması ve maliyet özeti (ders Bölüm 16) | 🟧 Should |
| F-25 | **Sohbet geçmişi**: önceki soru-cevapların saklanması ve tekrar açılması | 🟧 Should |
| F-26 | **MCP Server**: Claude Code / Copilot gibi bir asistanın Kovan'daki sayfalarda arama yapabilmesi (sadece okuma) | 🟧 Should |
| F-27 | **Hibrit arama**: kelime + anlamsal sonuçların birleştirilmesi | 🟨 Could |
| F-28 | Sohbet cevabının kelime kelime akarak gelmesi (streaming) | 🟨 Could |

### 3.5 Bu dönem yapılmayacaklar (⬜ Won't)

Kapsamın şişmemesi için bilinçli olarak dışarıda bırakıldı:

- Gerçek zamanlı ortak düzenleme
- Sayfa paylaşma, ekip/çalışma alanı, yetki yönetimi
- Notion'daki tablo/veritabanı görünümleri (board, takvim vb.) ve editörde tablo bloğu
- Görsel/dosya/video yükleme
- Şablonlar, favoriler, sayfa ikonları, kardeş sayfaları elle sıralama
- Mobil uygulama

---

## 4. Ekranlar

| Ekran | İçerik |
| --- | --- |
| **Giriş / Kayıt** | E-posta, şifre, (kayıtta) görünen ad |
| **Ana yerleşim** | Solda sayfa ağacı + "Yeni sayfa" + Arama + Sayfalarına Sor (+ Should: Çöp kutusu); sağda içerik |
| **Ana sayfa** | Karşılama; (Should) son düzenlenen sayfalar |
| **Sayfa** | Başlık, breadcrumb, blok editör, kaydetme ve indeks durumu, altta geri bağlantılar paneli |
| **Arama** | Arama kutusu, "Kelime / Anlamsal" seçimi, sonuç listesi (başlık + özet + skor) |
| **Sayfalarına Sor** | Soru kutusu, cevap, her cevabın altında kaynak sayfa bağlantıları; (Should) solda sohbet geçmişi |
| **Çöp kutusu** (Should) | Silinen sayfalar, geri al / kalıcı sil |

---

## 5. Yapay zekayı nerede kullanıyoruz?

Ders şartı: *"En az bir yapay zeka aracı; geliştirmede, üründe veya ikisinde."* Biz **ikisinde de** kullanıyoruz:

| Nerede | Nasıl |
| --- | --- |
| **Ürünün içinde** | Bulut **embedding API**'si ile sayfaların vektörlere çevrilmesi, Qdrant'ta anlamsal arama, bulut **dil modeli** (Claude / GPT / Gemini) ile kaynaklı cevap (RAG), (Should) MCP server |
| **Geliştirirken** | Claude Code, Codex, GitHub Copilot ile kod, test ve doküman üretimi. Kurallar `AGENTS.md`'de; prompt'lar ve yapay zekanın hataları `docs/ai-log.md`'de |

**Yerelde model çalıştırmak gerekmiyor.** Güçlü bilgisayarı olmayan ekip üyesi uygulamayı API anahtarı olmadan da **"fake" modda** çalıştırabilir (testler ve günlük geliştirme bu modda). Gerçek yapay zeka sadece `.env`'ye anahtar girilince devreye girer (ADR-006).

---

## 6. Kalite hedefleri (ders kriterleriyle bağlantılı)

| Hedef | Ölçüt |
| --- | --- |
| Kod kalitesi | SonarQube Cloud'da güvenilirlik, güvenlik ve bakım kolaylığı **A** |
| Test | Backend satır kapsamı ≥ %80, her Must kabul kriterine en az bir test |
| Arama kalitesi | ~21 soruluk (kişi başı 7) değerlendirme setinde doğru sayfanın ilk 5 sonuçta olma oranı ≥ %80 |
| Güvenlik | Bir kullanıcı başka kullanıcının içeriğine hiçbir yoldan (sayfa, arama, sohbet) erişemez; testle kanıtlı |
| Mimari | Katman kuralları import-linter ile CI'da otomatik denetlenir |

---

## 7. Kararlar

| Konu | Karar |
| --- | --- |
| Proje | ✅ P0007 – Notion klonu + anlamsal arama |
| Teslim | ✅ **25 Aralık 2026**; kod dondurma **13 Aralık** |
| Toplantılar | ✅ Hafta sonu |
| Repo | ✅ **Public**, adı **`sari-takim-kovan`** (SonarQube Cloud ücretsiz, hoca takip edebilir) |
| Takım adı | ✅ **Sarı Takım** (hocanın verdiği ad) |
| Dil modeli | ✅ **Bulut API** (Claude / GPT / Gemini); yerel model zorunlu değil |
| Çöp kutusu | ✅ Ekranı **Should**; silme Must |

### Hâlâ açık olanlar ❓

- [ ] **Sohbet modeli ve sağlayıcı**: Claude mı, GPT mi, Gemini mi? Fiyat karşılaştırması [ADR-006](docs/adr/ADR-006-llm-saglayici.md)'da. Kod hepsini destekleyecek; yalnızca `.env` değişir.
- [ ] **Embedding sağlayıcısı**: Claude'un embedding modeli yok. OpenAI `text-embedding-3-small`, BAAI `bge-m3` ve Voyage `voyage-4-lite` Sprint 2'de Türkçe notlarla küçük bir karşılaştırmayla denenip en iyisi seçilecek (ADR-006).
- [x] API anahtarlarının yönetimi: Sağlayıcı panelinde ortak bir organizasyon/proje, harcama limiti, herkesin kendi anahtarı (KURALLAR § 8). *Panel kurulumu, sağlayıcı seçilince yapılır.*
- [x] İş paketlerinin kişilere dağıtımı: eşit dağıtıldı ([docs/PLAN.md](docs/PLAN.md) § 3).
- [ ] İsim "Kovan" kalsın mı?
