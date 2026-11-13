# ADR-010: Test Stratejisi ve Kalite Araçları

## Durum

Kabul Edildi *(Accepted)* — 2026-11-13

## Bağlam

- Ders kriterleri: **test edilebilirlik** (birim + entegrasyon), **teknik borç** (ölçüm aracıyla A kalite), **okunabilirlik**, **mimari uyum**.
- Hocanın vurgusu: Fonksiyonlar kabul kriterlerine göre test edilecek.
- Kodun büyük kısmı yapay zeka ile üretilecek; doğruluğu ve kaliteyi **otomatik kapılar** kanıtlamalı (Bölüm 15: kabul ölçütü olarak testler).
- Hocanın lesson05 ADR-09'unda belirtilen eksik ("yalnızca birim test var, entegrasyon testi yok") bizde olmamalı.
- Repo **public** → SonarQube Cloud (eski adıyla SonarCloud) açık kaynak projeler için ücretsiz.

## Karar

- **Backend testleri:** pytest, pytest-cov, FastAPI `TestClient`, **Testcontainers** (gerçek PostgreSQL ve Qdrant), fake yapay zeka sağlayıcıları (ADR-006). Her test ilgili kabul kriterini `@pytest.mark.ac("AC-xx.y")` ile işaretler.
- **Frontend testleri:** Vitest + Testing Library. *(Should)* 3 Playwright duman testi.
- **Statik analiz:** ruff (lint + format), mypy, eslint, `tsc --noEmit`.
- **Mimari denetim:** **import-linter** (ADR-001, [mimari-secimi.md § 7](../mimari-secimi.md#7-uyumu-nasıl-kanıtlayacağız)).
- **Kod kalitesi:** **SonarQube Cloud**, GitHub Actions'tan her PR'da analiz. Hedef: güvenilirlik, güvenlik ve bakım kolaylığı derecelendirmeleri **A**, quality gate yeşil. Frontend kapsamı ortak quality gate'i kırmızıya düşürürse backend ve frontend iki ayrı Sonar projesi olarak analiz edilir. Rapor ekran görüntüsü README'ye eklenir.
- **Güvenlik taraması:** GitHub secret scanning + push protection, Dependabot uyarıları.
- **CI:** GitHub Actions; kırmızı CI ile merge yapılamaz (branch koruması). CI gerçek API anahtarı **kullanmaz**.

Ayrıntılar: [test-strategy.md](../test-strategy.md)

## Değerlendirilen alternatifler

| Alternatif | Neden seçilmedi |
| --- | --- |
| **Entegrasyon testlerinde SQLite / bellek içi sahte DB** | PostgreSQL'e özgü özellikler (JSONB, full-text, recursive CTE) test edilemez. |
| **Testlerde gerçek LLM** | Yavaş, deterministik değil, ücretli, anahtar ister. Gerçek model yalnızca RAG değerlendirme setinde. |
| **CodeClimate** | Ders rehberinde geçiyor; SonarQube derste kullanıldığı için tercih edildi. |
| **Yalnızca yerel SonarQube (Docker)** | Her PR'da otomatik kapı sağlamaz; repo public olduğu için SonarQube Cloud ücretsiz. Yerel SonarQube yedek seçenek. |
| **Çok sayıda uçtan uca test** | Yavaş ve kırılgan; 5 haftalık süreye uygun değil. 3 duman testi yeterli. |

## Sonuçlar

**Avantajlar:**
- Her kabul kriteri ↔ test eşleşmesi raporlanabilir (izlenebilirlik matrisi).
- Kalite, mimari ve test kapıları otomatik → hatalı yapay zeka kodu merge edilemez.
- Sunumda Sonar raporu, kapsam oranı ve `lint-imports` çıktısı somut kanıt olarak gösterilir.

**Değiş tokuşlar:**
- Testcontainers için CI ve geliştirici makinelerinde Docker gerekir; entegrasyon testleri birim testlerden yavaş.
- SonarQube Cloud kurulumu (organizasyon, token, workflow) Sprint 1'de zaman alır.
