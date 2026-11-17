# ADR-006: Bulut Dil Modeli ve Embedding Sağlayıcıları, Fake Çalışma Modu

## Durum

Kabul Edildi *(Accepted)* — 2026-11-13. **Sağlayıcı ve model seçimi ekip tarafından kesinleştirilecek** (§ Açık karar).

## Bağlam

- Ekip üyelerinin hepsinde yerel model çalıştıracak güçlü bilgisayar olmayabilir → **bulut API** tercih edildi (Claude, GPT, Gemini gibi).
- RAG için iki ayrı yapay zeka yeteneği gerekiyor: **embedding** (metin → vektör) ve **sohbet tamamlama** (kaynaklı cevap).
- **Anthropic'in kendi embedding modeli yok.** Resmi dokümanı embedding için Voyage AI'ı öneriyor. Yani Claude kullanılsa bile embedding için ayrı bir sağlayıcı gerekir.
- Testler ve CI para harcamamalı, internete çıkmamalı, deterministik olmalı. API anahtarı olmayan bir üye de uygulamayı çalıştırabilmeli.
- Repo **public**: Anahtarlar asla koda veya CI'a girmemeli.
- Kişisel notlar buluta gider → gizlilik (README "Aman Dikkat").

> "Claude Code" ve "Codex" **geliştirme araçlarıdır** (kodu yazmamıza yardım eder). Ürünün içindeki yapay zeka ise ilgili sağlayıcının **API**'si üzerinden, ayrı bir API anahtarı ve kullanım başı ücretle çalışır.

## Karar

1. `application` katmanında iki ayrı port: `EmbeddingProvider.embed(texts) -> vectors` ve `ChatModel.complete(system, messages, max_tokens) -> ChatCompletion` (metin + token kullanımı). Sağlayıcılar birbirinden bağımsız seçilir.
2. `infrastructure/ai/` altında **üç gerçek adaptör + fake'ler**:

| Adaptör | Kütüphane | Kapsadığı sağlayıcılar |
| --- | --- | --- |
| `AnthropicChatModel` | Resmi `anthropic` Python SDK | Claude |
| `OpenAICompatibleChatModel` | Resmi `openai` Python SDK + `base_url` | OpenAI (GPT), Google Gemini (OpenAI uyumlu uç nokta), istenirse yerel LM Studio/Ollama |
| `OpenAICompatibleEmbeddingProvider` | Resmi `openai` Python SDK + `base_url` | OpenAI embedding, Gemini embedding, OpenRouter üzerinden BAAI `bge-m3` |
| `FakeChatModel`, `FakeEmbeddingProvider` | — | Testler ve **fake çalışma modu** |

3. **Varsayılan mod `fake`** (`CHAT_PROVIDER=fake`, `EMBEDDING_PROVIDER=fake`): Anahtarsız çalışır; testler, CI ve günlük geliştirme bu modda. Gerçek yapay zeka `.env`'ye anahtar ve sağlayıcı girilince devreye girer.
4. Dış servis hataları (zaman aşımı 30 sn, 429, 5xx, bağlantı hatası) SDK'ların kendi yeniden denemesinden sonra `ExternalServiceError`'a çevrilir → API'de **503**, indeksleme döngüsünde yeniden deneme (ADR-005). Model güvenlik nedeniyle cevap vermeyi reddederse (`stop_reason == "refusal"`) kullanıcıya "Bu soruya cevap üretilemedi" mesajı döner.
5. Embedding modeli değişirse vektör boyutu değişebilir → `EMBEDDING_DIM` güncellenir ve `reindex --all` çalıştırılır.
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

Claude 5.5 modelleriyle ilgili uygulama notları: Opus 5.5'te düşünme kapatılamaz; maliyet/gecikme `effort` ayarıyla (sohbet için `low`) yönetilir. Kullanılan modele göre Anthropic'in reddetme (refusal) durumları için önerdiği yedek model (fallback) ayarı kod yazılırken eklenecek.

### Embedding modeli (metin → vektör)

> **Claude'un embedding modeli yoktur.** "Claude mu, GPT mi?" sorusu sadece sohbet modeli için geçerli. Embedding için aşağıdakilerden biri seçilir. Notlarımız **Türkçe** olduğu için Türkçe performansı belirleyici.

| Aday | Boyut | Fiyat (1M token) | Türkçe | Not |
| --- | --- | --- | --- | --- |
| **OpenAI `text-embedding-3-small`** | 1536 | ~$0.02 | Türkçe için yayımlanmış bir karşılaştırma bulamadık | En basit seçenek: ek adaptör gerekmez, kararlı, iyi belgelenmiş |
| **BAAI `bge-m3`** (açık kaynak; OpenRouter vb. üzerinden API) | 1024 | ~$0.01 | Türkçe karşılaştırmalarda üst sıralarda (TR-TEB, Türkçe soru-cevap testleri) | Çok dilli, 8K bağlam. Model açık kaynak, biz barındırmıyoruz; bir API sağlayıcısı üzerinden kullanılır |
| **Voyage AI `voyage-4-lite`** | 1024 | ~$0.02; **ilk 200M token ücretsiz** | Çok dilli olarak tanıtılıyor | Anthropic'in önerdiği sağlayıcı. Anahtar MongoDB Atlas'tan alınır; ödeme yöntemi eklenmezse hız limiti düşük olabilir. Seçilirse küçük bir adaptör eklenir |
| Google `gemini-embedding-001` | 3072 (küçültülebilir) | Ücretsiz katman var | — | Ücretsiz katmanda kota düşük, 429 hataları bildiriliyor. Yedek seçenek |

Bizim ölçeğimizde (birkaç yüz sayfa) **hepsi pratikte bedava**: Tüm proje boyunca 1–2 milyon token'ı geçmemesi beklenir, yani adayların hepsi < $0.05 tutar. Bu yüzden seçimi fiyat değil **Türkçe arama kalitesi** belirler.

#### Embedding seçimi: küçük bir karşılaştırma

Fazla abartmadan, 3 aday tek bir küçük betikle denenir:

1. **Adaylar:** OpenAI `text-embedding-3-small`, `bge-m3`, `voyage-4-lite`.
2. **Veri:** RAG değerlendirme setinin ilk hali: ~15 kurgusal Türkçe sayfa ve 20 soru (test-strategy § 6).
3. **Betik:** `eval/compare_embeddings.py`. Qdrant gerekmez; parçaları her modelle embed edip kosinüs benzerliğini bellekte hesaplar.
4. **Ölçüt:** Hit@5 ve MRR. Fark %5'ten azsa **en basit olan** seçilir (ek adaptör gerektirmeyen).
5. **Maliyet:** Toplam birkaç sent. **Zaman:** Sprint 2–3; ekip birlikte yapar (her üye bir adayı dener).
6. Sonuç tablosu README'ye ve bu ADR'ye yazılır. Bu tablo sunumda da "veriye dayalı karar" örneği olur.

### Açık karar (ekip)

- **Sohbet:** Claude mı, GPT mi, Gemini mi; hangi model? `.env` örneğinde `CHAT_MODEL=claude-opus-5-5` yazıyor; daha ucuz bir model seçmek ekibin bütçe kararıdır.
- **Embedding:** Yukarıdaki küçük karşılaştırmayla seçilir. Karşılaştırma yapılana kadar geliştirme fake modda sürer.
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
- [TR-TEB: Turkish Text Embedding Benchmark](https://www.researchgate.net/publication/407438143_TR-TEB_Turkish_Text_Embedding_Benchmark) · [TR-MTEB (EMNLP 2025 Findings)](https://aclanthology.org/2025.findings-emnlp.471.pdf) · [Türkçe soru-cevap getirme karşılaştırması (bge-m3)](https://github.com/ezgiieyice/ensemble-embeddings-semantic-search)
- [OpenRouter — BAAI bge-m3](https://openrouter.ai/baai/bge-m3) · [Voyage AI fiyatlandırma](https://docs.voyageai.com/docs/pricing)
