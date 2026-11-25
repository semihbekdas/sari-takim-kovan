# ADR-006: Bulut Dil Modeli ve Embedding Sağlayıcıları, Fake Çalışma Modu

## Durum

Kabul Edildi *(Accepted)* — 2026-11-13: port'lar, fake mod ve hata yönetimi. **2026-11-22:** Embedding modeli seçildi (OpenAI `text-embedding-3-small`). **Açık kalan:** sohbet modeli (§ Açık karar).

## Bağlam

- Ekip üyelerinin hepsinde yerel model çalıştıracak güçlü bilgisayar olmayabilir → **bulut API** tercih edildi (Claude, GPT, Gemini gibi).
- RAG için iki ayrı yapay zeka yeteneği gerekiyor: **embedding** (metin → vektör) ve **sohbet tamamlama** (kaynaklı cevap).
- **Anthropic'in kendi embedding modeli yok.** Resmi dokümanı embedding için Voyage AI'ı öneriyor. Yani Claude kullanılsa bile embedding için ayrı bir sağlayıcı gerekir.
- Testler ve CI para harcamamalı, internete çıkmamalı, deterministik olmalı. API anahtarı olmayan bir üye de uygulamayı çalıştırabilmeli.
- Repo **public**: Anahtarlar asla koda veya CI'a girmemeli.
- Kişisel notlar buluta gider → gizlilik (ders reposunun README'sindeki "Aman Dikkat" bölümü).

> "Claude Code" ve "Codex" **geliştirme araçlarıdır** (kodu yazmamıza yardım eder). Ürünün içindeki yapay zeka ise ilgili sağlayıcının **API**'si üzerinden, ayrı bir API anahtarı ve kullanım başı ücretle çalışır.

## Karar

1. `application` katmanında iki ayrı port: `EmbeddingProvider.embed(texts) -> vectors` ve `ChatModel.complete(system, messages, max_tokens) -> ChatCompletion` (metin, bitiş nedeni ve token kullanımı). Sağlayıcılar birbirinden bağımsız seçilir.
2. `infrastructure/ai/` altında **üç gerçek adaptör + fake'ler**:

| Adaptör | Kütüphane | Kapsadığı sağlayıcılar |
| --- | --- | --- |
| `AnthropicChatModel` | Resmi `anthropic` Python SDK | Claude |
| `OpenAICompatibleChatModel` | Resmi `openai` Python SDK + `base_url` | OpenAI (GPT), Google Gemini (OpenAI uyumlu uç nokta), OpenRouter (bge-m3) |
| `OpenAICompatibleEmbeddingProvider` | Resmi `openai` Python SDK + `base_url` | OpenAI embedding, Gemini embedding, OpenRouter üzerinden BAAI `bge-m3` |
| `FakeChatModel`, `FakeEmbeddingProvider` | — | Testler ve **fake çalışma modu** |

3. **Varsayılan mod `fake`** (`CHAT_PROVIDER=fake`, `EMBEDDING_PROVIDER=fake`): Anahtarsız çalışır; testler, CI ve günlük geliştirme bu modda. Gerçek yapay zeka `.env`'ye anahtar ve sağlayıcı girilince devreye girer.
4. Dış servis hataları (zaman aşımı `AI_TIMEOUT_SECONDS` = 30 sn, 429, 5xx, bağlantı hatası) SDK'nın tek yeniden denemesinden sonra (en kötü durumda ~60 sn) `ExternalServiceError`'a çevrilir → API'de **503**, indeksleme döngüsünde yeniden deneme (ADR-005). Model güvenlik nedeniyle cevap vermeyi reddederse (`stop_reason == "refusal"`) kullanıcıya "Bu soruya cevap üretilemedi" mesajı döner.
5. Embedding modeli değişirse vektör boyutu değişebilir → `EMBEDDING_DIM` güncellenir ve indeks yeniden üretilir (ADR-005, "Kurtarma").
6. Token kullanımı her çağrıda yapay zeka adaptörlerinde loglanır (Should, US-16).

## Seçenekler ve maliyet

### Sohbet modeli (cevap üretme)

| Sağlayıcı / model | Model kimliği | Fiyat (girdi / çıktı, 1M token başına) | Soru başına tahmini maliyet* |
| --- | --- | --- | --- |
| Claude Opus 5.5 | `claude-opus-5-5` | $4 / $20 | ~$0.022 |
| Claude Sonnet 5.5 | `claude-sonnet-5-5` | $2 / $10 | ~$0.011 |
| Claude Haiku 5.5 | `claude-haiku-5-5` | $0.10 / $0.50 | ~$0.0006 |
| OpenAI GPT | güncel model, OpenAI dokümantasyonundan | sağlayıcı fiyat sayfası | — |
| Google Gemini | güncel model, Google AI Studio dokümantasyonundan | ücretsiz katman + ücretli | — |

\* ~3.000 girdi token'ı (6 parça + talimat + soru) ve ~500 çıktı token'ı varsayımıyla; modelin düşünme (thinking) token'ları hariç. Claude fiyatları Anthropic'in birinci taraf API fiyatlarıdır (Kasım 2026).

**Örnek:** Geliştirme + demo boyunca 500 soru → Opus 5.5 ≈ $11, Sonnet 5.5 ≈ $5.5, Haiku 5.5 ≈ $0.3.

Claude 5.5 modelleriyle ilgili uygulama notları: Opus 5.5'te düşünme kapatılamaz; maliyet/gecikme `effort` ayarıyla (sohbet için `low`) yönetilir. Kullanılan modele göre Anthropic'in reddetme (refusal) durumları için önerdiği yedek model (fallback) ayarı `infrastructure/ai/anthropic_chat.py`'de açıktır (`fallbacks="default"`).

### Embedding modeli (metin → vektör)

> **Claude'un embedding modeli yoktur.** "Claude mu, GPT mi?" sorusu sadece sohbet modeli için geçerli. Embedding için aşağıdakilerden biri seçilir. Notlarımız **Türkçe** olduğu için Türkçe performansı belirleyici.

| Aday | Boyut | Fiyat (1M token) | Türkçe arama (yayımlanmış sonuç) | Not |
| --- | --- | --- | --- | --- |
| **OpenAI `text-embedding-3-small`** ✅ *seçildi* | 1536 | $0.02 | TR-MTEB'de arama puanı **64,99**: tablonun en yükseği (`multilingual-e5-large` 60,62). Model 768 boyuta indirilmiş hâliyle ölçülmüş | Kodda varsayılan model: ek adaptör ve ayar gerekmez, kararlı, iyi belgelenmiş. Hesaba en az $5 kredi yüklenir (1 yıl geçerli) |
| BAAI `bge-m3` (açık kaynak; OpenRouter üzerinden `baai/bge-m3`) · *yedek* | 1024 | $0.01 | TR-TEB'de arama puanı 59,30: açık kaynak modeller arasında ikinci (`multilingual-e5-large` 58,57). TR-TEB yalnızca açık kaynak modelleri ölçer | Sorguya ayrı talimat gerektirmez, yani `embed(texts)` arayüzümüze doğrudan uyar. OpenRouter kredi alımında %5,5 (en az $0.80) ücret alır |
| Qwen `qwen3-embedding-8b` (OpenRouter) | 4096 | $0.01 | TR-TEB'de genel sıralamada birinci (64,58), aramada 59,62 | Sorgular için talimat metni öneriyor; talimatsız kullanımda %1–5 düşüş bildiriyor. Arayüzümüze sorgu/doküman ayrımı eklemek gerekir |
| Voyage AI `voyage-4-lite` | 1024 | $0.02; **ilk 200M token ücretsiz** | Yayımlanmış Türkçe sonuç bulunamadı | Anthropic'in önerdiği sağlayıcı. Anahtar MongoDB Atlas'tan alınır; OpenAI uyumlu adaptörümüzle çalışıp çalışmadığı denenmedi |
| Google `gemini-embedding-001` | 3072 (küçültülebilir) | $0.15; ücretsiz katman var | Yayımlanmış Türkçe sonuç bulunamadı | Ücretsiz katmanda kota düşük, 429 hataları bildiriliyor |

Fiyatlar 22 Kasım 2026'da sağlayıcıların kendi sayfalarından alındı (Kaynaklar).

Bizim ölçeğimizde (birkaç yüz sayfa) **hepsi pratikte bedava**: Tüm proje boyunca 1–2 milyon token'ı geçmemesi beklenir, yani adayların hepsi < $0.05 tutar. Bu yüzden seçimi fiyat değil **Türkçe arama kalitesi** belirler.

#### Embedding seçimi (22 Kasım 2026)

**Karar: OpenAI `text-embedding-3-small`.** Gerekçe:

1. **Türkçe kanıt.** TR-MTEB (EMNLP 2025, Tablo 2) Türkçe arama görevlerinde bu modele 64,99 veriyor; tablodaki en yüksek puan. `bge-m3`'ün ölçüldüğü TR-TEB'de (LREC 2026, Tablo 4) `bge-m3` ile `multilingual-e5-large` arasındaki fark 0,7 puan. İki tabloda da bulunan `multilingual-e5-large` ölçü alınırsa `text-embedding-3-small` en az `bge-m3` kadar iyi görünüyor. Bu dolaylı bir karşılaştırmadır: İki ayrı çalışma, iki ayrı veri kümesi.
2. **Basitlik.** Kodda varsayılan model; `.env`'ye yalnızca `EMBEDDING_PROVIDER=openai_compatible` ve anahtar girilir.
3. **Maliyet.** Proje boyunca beklenen 1–2 milyon token yaklaşık $0.02–0.04 tutar.

**Karşı kanıt.** Türkçe içermeyen çok dilli arama ölçümü MIRACL tersini gösteriyor: `bge-m3` 69,2; `text-embedding-3-large` 54,9; `text-embedding-3-small` 44,0. Karar bu yüzden Türkçe ölçümlere dayandırıldı ve kendi verimizle doğrulanacak.

**Vazgeçilen plan.** İlk planda üç aday (OpenAI, `bge-m3`, Voyage) üç ayrı hesapla denenecekti. Yayımlanmış Türkçe sonuçlar adayları zaten sıraladığı için bundan vazgeçildi: Ödev ölçeğinde üç hesap, üç anahtar ve üç ölçüm gereksiz iş.

**Doğrulama.** Seçilen model kendi değerlendirme setimizle ölçülür: ~15 kurgusal Türkçe sayfa ve ~21 soru (kişi başı 5 sayfa + 7 soru), `eval/compare_embeddings.py`, ölçütler Hit@5 ve MRR, hedef Hit@5 ≥ 0,8 (test-strategy § 6). Hedef tutmazsa aynı betikle `bge-m3` denenir; bunun için yalnızca `EMBEDDING_BASE_URL=https://openrouter.ai/api/v1`, `EMBEDDING_MODEL=baai/bge-m3` ve `EMBEDDING_DIM=1024` değişir, sonra indeks yeniden üretilir (ADR-005, "Kurtarma"). Sonuç tablosu README'ye ve bu ADR'ye yazılır.

### Açık karar (ekip)

- **Sohbet:** Claude mı, GPT mi, Gemini mi; hangi model? `.env` örneğinde `CHAT_MODEL=claude-opus-5-5` yazıyor; daha ucuz bir model seçmek ekibin bütçe kararıdır. Embedding için açılan OpenAI anahtarı bir GPT modeliyle sohbet için de kullanılabilir (`CHAT_PROVIDER=openai_compatible`); böylece tek anahtar yeter. Karar, "Sayfalarına Sor" bağlanırken (Sprint 3) verilir.
- **Embedding:** ✅ Seçildi (yukarıda). Günlük geliştirme ve testler yine fake modda sürer.
- Seçim yapılınca bu ADR'nin "Durum" satırı güncellenir.

## Değerlendirilen alternatifler

| Alternatif | Neden seçilmedi |
| --- | --- |
| **Yerel model (LM Studio / Ollama)** varsayılan | Her üyenin bilgisayarı yeterli olmayabilir; küçük modellerin cevap kalitesi düşük. Yine de `OpenAICompatible…` adaptörü yerel uç noktayla da çalışır. |
| **Tek bir sağlayıcıya kilitlenmek** | Fiyat/kota değişince tüm kod değişir; testte mock zorlaşır. |
| **Claude'u OpenAI uyumlu bir aracı üzerinden çağırmak** | Claude için resmi `anthropic` SDK kullanılır; aracı katmanlar özellikleri ve hata tiplerini kaybettirir. |
| **LangChain / LlamaIndex** | Hızlı başlatır ama soyutlama kalın; RAG akışını kendimiz yazmak hem öğrenme hem "koda hakimiyet" (sunum) açısından daha iyi. Dersteki örnekler de çerçevesiz. |

## Sonuçlar

**Avantajlar:**
- Güçlü bilgisayar gerekmez; anahtarı olmayan üye de fake modda tam uygulamayı çalıştırır.
- Sağlayıcı değişimi yalnızca `.env` değişikliği.
- Testler ücretsiz, hızlı ve deterministik.
- RAG mantığı (getirme, prompt, atıf) tamamen bizim kodumuz: test edilebilir ve anlatılabilir.

**Değiş tokuşlar:**
- Kullanım başı ücret ve kota (harcama limiti şart; KURALLAR § 8).
- Notlar bulut sağlayıcıya gider → demo verisi kurgusal olmalı.
- İki ayrı sağlayıcı (sohbet + embedding) iki ayrı anahtar demek olabilir.
- Fake mod gerçek arama kalitesini göstermez; kalite RAG değerlendirme setiyle gerçek modelde ölçülür.

## Kaynaklar

- Anthropic — [Embeddings](https://platform.claude.com/docs/en/build-with-claude/embeddings) ("Anthropic does not offer its own embedding model"; Voyage AI önerisi)
- Google — [Gemini API OpenAI compatibility](https://aistudio.google.com/docs/openai) (OpenAI SDK ile sohbet ve embedding)
- OpenAI — [text-embedding-3-small](https://developers.openai.com/api/docs/models/text-embedding-3-small)
- [TR-MTEB (EMNLP 2025 Findings)](https://aclanthology.org/2025.findings-emnlp.471.pdf), Tablo 2 · [TR-TEB: Turkish Text Embedding Benchmark (LREC 2026)](https://aclanthology.org/2026.lrec-1.862/), Tablo 4 · [Türkçe soru-cevap getirme karşılaştırması (bge-m3)](https://github.com/ezgiieyice/ensemble-embeddings-semantic-search)
- MIRACL sonuçları: [BGE M3-Embedding makalesi](https://arxiv.org/abs/2402.03216), Tablo 1 · [OpenAI: New embedding models and API updates](https://openai.com/index/new-embedding-models-and-api-updates/)
- [BAAI/bge-m3 model kartı](https://huggingface.co/BAAI/bge-m3) · [Qwen3-Embedding-8B model kartı](https://huggingface.co/Qwen/Qwen3-Embedding-8B)
- [OpenRouter embedding modelleri ve fiyatları](https://openrouter.ai/collections/embedding-models) · [OpenRouter SSS (ücretler)](https://openrouter.ai/docs/faq) · [Voyage AI fiyatlandırma](https://docs.voyageai.com/docs/pricing) · [Gemini API fiyatlandırma](https://aistudio.google.com/docs/pricing) · [OpenAI ön ödemeli faturalandırma](https://help.openai.com/en/articles/8264644-how-does-prepaid-billing-work)
