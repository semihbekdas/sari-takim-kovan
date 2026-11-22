# Yapay Zeka Kullanım Günlüğü

> Ders kriteri: *"Kullanılan yapay zeka araçları ve kullanım şekli proje dokümantasyonunda açıkça belirtilmelidir."*
> Bu günlük README'deki **"Kullanılan Yapay Zeka Araçları"** ve **"Karşılaşılan Zorluklar ve Çözümler"** bölümlerinin kaynağıdır. Önemli her yapay zeka etkileşimi kısa bir kayıt olarak eklenir.

## Kim nereye yazar?

Herkes **kendi dosyasına** yazar; böylece aynı anda açılan PR'lar bu dosyalarda çakışmaz. Yeni kayıt dosyanın **en altına** eklenir.

| Dosya | İçerik |
| --- | --- |
| [ortak.md](ortak.md) | Projenin başlangıcındaki planlama oturumları ve ekip kararları |
| [semih.md](semih.md) | Semih (İP-C: yapay zeka, backend iskeleti, CI) |
| [ozlem.md](ozlem.md) | Özlem (İP-B: kimlik, içerik ve arama) |
| [umut.md](umut.md) | Umut (İP-A: sayfalar, editör, docker-compose, frontend) |

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

> **📝 `✍️ DOLDURULACAK` yazan yerler ne demek?** Kayıtlarda yapay zekanın ne ürettiği yazılı, ama **sizin ne yaptığınız** henüz yazılı değil, çünkü henüz bir şey yapmadınız. Ders "Agentic Engineering" istiyor: Yapay zekanın çıktısını okumak, yanlışını bulmak, düzeltmek. Bu alanlar o işin kanıtı.
> - **Kim:** Claude Code oturumunu yürüten üyenin adı.
> - **Bizim müdahalemiz:** Dokümanları okuyunca neyi değiştirdiniz, neyi sildiniz, neye itiraz ettiniz? Örnek: *"Sprint 3'ü fazla yüklü bulduk, kelime aramasını Sprint 2'ye aldık."* veya *"İsim önerisini 'sari-takim-kovan' olarak kesinleştirdik."* Hiçbir şey değiştirmediyseniz "okundu, değişiklik yok" yazın. Boş bırakmayın.
> - Her üye, Sprint 1'deki doküman okuma PR'ında kendi iş paketinin dokümanlarını okuyup kendi dosyasına ayrı bir kayıt ekler (PLAN § 5).
