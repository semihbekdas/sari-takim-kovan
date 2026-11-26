# RAG Değerlendirme Seti

Arama ve "Sayfalarına Sor" kalitesini **gerçek modelle** ölçmek için kurgusal bir not seti ve sorular (docs/test-strategy.md § 6, ADR-006).

> **Gerçek kişisel veri koymayın.** Sayfalar kurgusaldır; gerçek modele gönderildiğinde bulut sağlayıcıya gider.

## Klasör yapısı

```
eval/
├── dataset/<isim>/<sayfa-adi>.md    # her üyenin ~5 sayfası (Markdown)
├── questions/<isim>.toml            # her üyenin ~7 sorusu
└── compare_embeddings.py            # bir embedding modelini bu setle ölçen betik
```

Herkes **kendi klasörüne ve kendi dosyasına** yazar; böylece aynı dosyada çakışma olmaz.

## Sayfa biçimi (Markdown)

- İlk satır sayfa başlığıdır: `# Başlık`
- Bölümler `## Alt başlık` ile ayrılır. Ölçüm betiği her bölümü ayrı bir parça olarak kullanır.
- Bir bölüm en fazla **1000 karakter** olabilir; betik daha uzun bölümde durur. Uygulama bu sınırı (`CHUNK_MAX_CHARS`, ADR-009) aşan bölümü böldüğü için, ölçülen parçalar ancak böyle uygulamanın indeksleyeceği parçalarla aynı kalır.
- Sayfanın kimliği `klasör/dosya-adı`dır: `dataset/semih/otomobil-servis-notlari.md` → `semih/otomobil-servis-notlari`. Dosya adında Türkçe karakter ve boşluk kullanmayın.
- Başlık yalnızca ilk `# ` satırıdır; gövdedeki `# ` satırları (ör. kod yorumu) metin sayılır.

## Soru biçimi (TOML)

```toml
[[question]]
id = "isim-01"                          # benzersiz
type = "normal"                         # normal | synonym | not_found | injection
question = "Soru metni?"
expected_pages = ["sayfa-adi"]          # zorunlu; kendi klasörünüzdeki sayfa (başka üyeninki: "uye/sayfa-adi"); not_found ise []
must_not_contain = ["HACKLENDİ"]        # isteğe bağlı (injection); cevap değerlendirme betiği gelince kullanılır
note = "Açıklama"                       # isteğe bağlı
```

| Tür | Ne ölçer? | Herkes en az |
| --- | --- | --- |
| `normal` | Soru, sayfadaki kelimelerle soruluyor | 3 |
| `synonym` | Soru farklı kelimelerle soruluyor ("araba" ↔ "otomobil"), anlamsal arama gerekir (AC-10.1) | 2 |
| `not_found` | Notlarda cevap yok; sistem "bulamadım" demeli (AC-11.2) | 1 |
| `injection` | Sayfada modele talimat vermeye çalışan bir metin var; cevap bunu uygulamamalı (AC-11.4) | 1 |

## Embedding ölçümü

Seçilen model OpenAI `text-embedding-3-small` (gerekçesi: ADR-006). Bu set o seçimi kendi verimizle doğrular; hedef Hit@5 ≥ 0,8. Hedef tutmazsa aynı betik yedek modelle bir kez daha çalıştırılır.

Komutlar **repo kökünden** çalıştırılır. Betik, hatalı bir soruda açıklayıcı bir hatayla durur: bilinmeyen `type`, olmayan bir sayfa adı, `not_found` dışındaki bir türde boş `expected_pages` veya `not_found` sorusunda dolu `expected_pages`.

```bash
# Anahtarsız deneme (betiğin çalıştığını görmek için; sonuçlar anlamlı değildir)
uv run --project backend python eval/compare_embeddings.py --provider fake

# Gerçek model (anahtar ortam değişkeninden okunur, koda yazılmaz)
EMBEDDING_API_KEY=... uv run --project backend python eval/compare_embeddings.py \
  --base-url https://api.openai.com/v1 --model text-embedding-3-small --dim 1536
```

| Model | `--base-url` | `--model` | `--dim` |
| --- | --- | --- | --- |
| OpenAI (seçilen) | `https://api.openai.com/v1` | `text-embedding-3-small` | 1536 |
| BAAI bge-m3 (yedek; OpenRouter) | `https://openrouter.ai/api/v1` | `baai/bge-m3` | 1024 |

Çıktı, Markdown tablosu halinde **Hit@1, Hit@5, MRR** değerlerini ve arama eşiği için iki skoru verir: beklenen sayfaların en düşük skoru ve "notlarda yok" sorularının en yüksek skoru. `SEARCH_MIN_SCORE` bu ikisinin arasında seçilir; eşik beklenen sayfanın skorundan yüksek olursa doğru sonuç da elenir. Sonuçlar ADR-006'ya ve README'ye eklenir.

Betiği değiştirirseniz `backend/` içinde `uv run ruff check . ../eval`, `uv run ruff format --check . ../eval` ve `uv run mypy` temiz olmalıdır; CI aynılarını çalıştırır.
