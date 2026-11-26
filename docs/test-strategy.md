# Test Stratejisi

> Ders kriteri: *"Kodun birim testleri ve entegrasyon testleri ile ne kadar test edilebilir olduğuna bakılır."* Hocanın derste vurgusu: **fonksiyonlar/metotlar kabul kriterlerine göre test edilecek.**
> Karar kaydı: [ADR-010](adr/ADR-010-test-ve-kalite.md)

---

## 1. Test piramidi

```
             ▲    Uçtan uca (Playwright, Could)    3 duman senaryosu
           ▲▲▲    Kabul (API senaryoları)           her Must AC ≥ 1 test, gerçek DB + fake yapay zeka
        ▲▲▲▲▲▲    Entegrasyon (Testcontainers)      repository'ler, Qdrant adaptörü, indeksleme döngüsü
   ▲▲▲▲▲▲▲▲▲▲▲    Birim (pytest / Vitest)           domain kuralları, servisler, chunking, prompt, UI mantığı
```

| Seviye | Ne test edilir | Araç | Bağımlılıklar | Klasör |
| --- | --- | --- | --- | --- |
| **Birim** | Domain kuralları (R-xx), `PageContent`, `chunk_page`, `build_prompt`, atıf ayrıştırma, servisler (port'lar fake) | pytest | Yok (milisaniyeler) | `backend/tests/unit/` |
| **Entegrasyon** | SQL repository'leri, Qdrant adaptörü (`owner_id` filtresi!), indeksleme döngüsü (yeniden deneme, idempotency, eski parçaların silinmesi) | pytest + **Testcontainers** (PostgreSQL, Qdrant) | Gerçek PostgreSQL ve Qdrant, **fake** embedding | `backend/tests/integration/` |
| **Kabul (API)** | Kabul kriterleri, HTTP üzerinden (kayıt → sayfa → indeks → arama → sohbet) | pytest + FastAPI `TestClient` | Gerçek DB'ler, **fake** yapay zeka | `backend/tests/acceptance/` |
| **Frontend** | Otomatik kaydetme (debounce), 409 uyarısı, bağlantı gösterimi, API istemcisi | Vitest + Testing Library (API istemcisi mock'lanır) | Yok | `frontend/tests/` |
| **Uçtan uca** *(Could)* | 3 duman senaryosu: giriş → sayfa yaz → ara; bağlantı + geri bağlantı; sohbet + kaynak | Playwright | Tüm sistem, fake yapay zeka | `frontend/e2e/` |
| **RAG değerlendirme** | Getirme kalitesi (Hit@5, MRR), "bulamadım" doğruluğu, prompt injection | Kendi betiğimiz | **Gerçek** embedding ve dil modeli (ücretli, elle çalıştırılır) | `eval/` |

## 2. Fake'ler (testler internete çıkmaz, para harcamaz)

| Port | Testteki karşılığı | Davranış |
| --- | --- | --- |
| `EmbeddingProvider` | `FakeEmbeddingProvider` | Kelimelerden deterministik vektör (hash tabanlı, normalize). Ortak kelimesi olan metinler benzer çıkar |
| `ChatModel` | `FakeChatModel` | Programlanabilir cevap; aldığı prompt'u saklar (prompt içeriği assert edilebilir) |
| İkisi de | Testte yazılan küçük bir hata fake'i | `ExternalServiceError` fırlatır (503 ve yeniden deneme senaryoları) |
| Zaman | Servise parametre olarak verilen sabit bir an | Zamanı kontrol eder (10 sn bekleme, yeniden deneme süreleri) |

Bu fake'ler aynı zamanda uygulamanın **`fake` çalışma modudur** (ADR-006): API anahtarı olmayan ekip üyesi uygulamayı uçtan uca çalıştırabilir.

> AC-10.1 gibi **gerçek anlam** gerektiren kriterler fake ile kanıtlanamaz. Bunlar **RAG değerlendirme setinde** gerçek modelle ölçülür (§ 6).

## 3. Test yazım kuralları

- İsimlendirme: `test_<ne>_<koşul>_<beklenen>` → `test_move_page_under_own_descendant_raises_cycle_error`
- Yapı **Arrange – Act – Assert**, test başına tek davranış.
- Bir kabul kriterini doğrulayan her test o kriteri işaretler (`pyproject.toml`'da `ac` işareti kayıtlı); altyapı testleri (ör. sağlık, adaptör ayrıntıları) işaretsiz olabilir:

```python
@pytest.mark.ac("AC-05.5")
def test_move_page_under_own_descendant_raises_cycle_error(page_service, tree):
    with pytest.raises(DomainRuleError) as err:
        page_service.move(owner_id=tree.owner, page_id=tree.root, new_parent_id=tree.grandchild)
    assert err.value.rule_code == "R-05"
```

- Hata yolları da test edilir: geçersiz girdi, yetkisiz erişim, servis kapalı, sürüm çakışması.
- **Yasak:** assert'siz test, `skip` ile kapatma, test silme, coverage'ı şişirmek için dosya hariç tutma. Tek istisna: Docker gerektiren entegrasyon testleri yerelde Docker kapalıysa atlanır; CI'da Docker zorunludur ve yoksa test hata verir (`tests/integration/containers.py`).
- Testler birbirinden bağımsızdır; her entegrasyon testi temiz veriyle başlar.

## 4. Kapsam hedefleri

| Alan | Satır kapsamı hedefi |
| --- | --- |
| `domain` + `application` | ≥ %90 |
| Backend genel | ≥ %80 |
| Frontend | Oran hedefi yok; mantık içeren kısımlar test edilir (otomatik kaydetme, 409 uyarısı, bağlantı gösterimi, API istemcisi) |

Kapsam bir araçtır, amaç değildir. Frontend kodu da Sonar'da analiz edilir (güvenilirlik, güvenlik ve bakım kolaylığı dereceleri); Sonar'ın kapsam koşulu ise yalnızca backend için geçerlidir (`sonar.coverage.exclusions=frontend/**`). Gerekçe: Ekran bileşenlerini %80 kapsama çıkarmak bu projede getirdiğinden fazla iş demektir; frontend'de mantık içeren kısımlar Vitest ile test edilir (ADR-010).

## 5. AC izlenebilirlik matrisi

Tablo, kod dondurmadan önce `grep -rn 'pytest.mark.ac' backend/tests` çıktısından bir kez güncellenir *(Ortak / Sprint 4)*; ayrı bir betik yazılmaz. Tablodaki test adları planlanan adlardır:

| AC | Seviye | Planlanan test |
| --- | --- | --- |
| AC-01.1 | Kabul | `test_register_with_valid_data_returns_201_without_password` |
| AC-01.2 | Kabul | `test_register_with_existing_email_case_insensitive_returns_409` |
| AC-01.3 | Birim + Kabul | `test_register_with_short_password_returns_422` |
| AC-01.4 | Entegrasyon | `test_registered_user_password_is_stored_as_argon2_hash` |
| AC-02.1 | Kabul | `test_login_sets_httponly_samesite_strict_cookie` |
| AC-02.2 | Kabul | `test_login_with_wrong_password_returns_generic_401` |
| AC-02.3 | Kabul | `test_logout_clears_cookie_and_blocks_access` |
| AC-02.4 | Kabul + Frontend | `test_protected_endpoint_without_session_returns_401` |
| AC-02.5 🟧 | Kabul | `test_sixth_failed_login_within_minute_returns_429` |
| AC-03.1 | Birim | `test_page_with_blank_title_gets_default_title` |
| AC-03.2 | Birim | `test_page_title_longer_than_200_raises_rule_r03` |
| AC-03.3 | Kabul | `test_get_own_page_returns_content_version_status_breadcrumbs` |
| AC-03.4 | Kabul | `test_get_other_users_page_returns_404` |
| AC-04.1 | Frontend | `autosave.test.ts › saves 1s after typing stops` |
| AC-04.2 | Kabul | `test_saved_content_round_trips_all_allowed_block_types` |
| AC-04.3 | Birim + Kabul + Frontend | `test_update_with_stale_version_returns_409` |
| AC-04.4 | Birim | `test_content_with_table_block_is_rejected` |
| AC-04.5 | Entegrasyon | `test_update_increments_version_and_marks_page_pending` |
| AC-05.1 | Kabul | `test_child_page_appears_under_parent_sorted_by_title` |
| AC-05.2 | Kabul | `test_breadcrumbs_list_ancestors_in_order` |
| AC-05.3 | Kabul | `test_create_page_under_other_users_parent_returns_404` |
| AC-05.4 🟧 | Kabul | `test_move_page_moves_whole_subtree` |
| AC-05.5 🟧 | Birim | `test_move_page_under_own_descendant_raises_cycle_error` |
| AC-06.1 | Kabul | `test_deleted_page_and_children_hidden_from_tree_search_chat` |
| AC-06.2 | Entegrasyon | `test_deleted_page_vectors_removed_by_index_loop` |
| AC-06.3–06.5 🟧 | Kabul | `test_trash_*` |
| AC-07.1–07.2 | Frontend | `page-mention.test.tsx` |
| AC-07.3 | Frontend | `page-mention.test.tsx › shows deleted page` (başlıklar sayfa ağacından) |
| AC-08.1–08.4 🟧 | Birim + Kabul | `test_backlinks_*` |
| AC-09.1–09.3 🟧 | Kabul | `test_keyword_search_*` |
| AC-10.1 | RAG değerlendirme | `eval/questions.yaml` (eşanlamlı sorular) |
| AC-10.2 | Entegrasyon + Kabul | `test_semantic_search_never_returns_other_users_chunks` |
| AC-10.3 | Kabul | `test_search_reflects_updated_content_after_indexing` |
| AC-10.4 | Kabul | `test_semantic_search_hides_deleted_page_immediately` |
| AC-10.5 | Kabul | `test_semantic_search_returns_503_when_embedding_down` |
| AC-11.1 | Birim + Kabul | `test_chat_answer_contains_valid_citations` |
| AC-11.2 | Birim | `test_chat_without_relevant_chunks_does_not_call_llm` |
| AC-11.3 | Kabul | `test_chat_context_contains_only_own_chunks` |
| AC-11.4 | Birim + RAG değerlendirme | `test_prompt_wraps_context_in_delimiters_and_forbids_instructions` |
| AC-11.5 | Kabul | `test_chat_returns_503_when_llm_unavailable` |
| AC-11.6 | Birim | `test_unknown_citation_numbers_are_dropped` |
| AC-12.1 | Kabul + Frontend | `test_page_index_status_transitions` |
| AC-12.2 | Entegrasyon | `test_failed_indexing_retried_with_backoff_then_marked_failed` |
| AC-12.3 | Entegrasyon | `test_indexing_same_version_twice_is_idempotent` |
| AC-12.4 | Entegrasyon | `test_rapid_saves_trigger_single_embedding_call_after_settle` |
| AC-12.5 | Entegrasyon | `test_shrinking_content_removes_stale_chunks` |
| AC-13.x, AC-14.1, AC-16.x 🟧 · AC-15.x 🟨 | Kabul / Birim | İlgili iş başlarken eklenir |

## 6. RAG değerlendirmesi

- `eval/dataset/<isim>/*.md`: Her üyenin 5 kurgusal sayfası (toplam ~15). **Gerçek kişisel veri kullanılmaz.** Biçim: `eval/README.md`.
- `eval/questions/<isim>.toml`: Her üyenin 7 sorusu (toplam ~21), her biri için beklenen kaynak sayfa(lar). Türler: `normal`, `synonym` (AC-10.1), `not_found` (AC-11.2), `injection` (AC-11.4).
- Metrikler: **Hit@5**, **MRR**, "bulamadım" doğruluğu. Seçilen embedding modeli (ADR-006) `eval/compare_embeddings.py` ile ölçülür; hedef tutmazsa aynı betikle ikinci bir model denenir.
- Hedef: Hit@5 ≥ 0.8. `RAG_TOP_K`, `SEARCH_MIN_SCORE` ve parça boyutu bu sete göre ayarlanır; sonuç tablosu README'ye yazılır.
- Gerçek API kullandığı için elle ve seyrek çalıştırılır (her sprint sonunda bir kez).

## 7. CI'da çalışan kontroller

```
ruff check · ruff format --check · mypy · lint-imports
pytest (unit + integration + acceptance) --cov
vitest · eslint · prettier · tsc --noEmit
SonarQube Cloud analizi + quality gate
(Could: Playwright duman testleri, main'e merge sonrası)
```
