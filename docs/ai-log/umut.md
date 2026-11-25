# Yapay Zeka Kullanım Günlüğü — Umut

> Umut'un (İP-A) kayıtları. Şablon ve kurallar: [README.md](README.md). Kayıtlar tarih sırasıyla, en yenisi en altta.

### 2026-11-20 — Umut: doküman okuma (#2)
- **Kim:** Umut
- **Araç / model:** Claude (claude.ai)
- **Amaç:** İP-A ile ilgili dokümanları (README, KURALLAR, PLAN, architecture, domain-design, ADR-003, ADR-004, ADR-007) okumak ve kendi işlerim (#3 docker-compose + Alembic, #4 frontend iskeleti) öncesi eksikleri görmek.
- **Prompt (özet):** "Bana atanan issue'ları ve ilgili dokümanları anlat; ilk doküman PR'ım için adım adım yardım et."
- **Sonuç:** İP-A kapsamı ve Sprint 1–2 işlerim netleşti. Dokümanlarda Alembic ve qdrant-client kullanılacağı yazıyor ama `backend/pyproject.toml`'da henüz bağımlılık olarak yoklar; bunlar #3'te eklenecek.
- **Yapay zekanın hataları / eksikleri:** Önemli bir hata görmedim.
- **Bizim müdahalemiz:** Okundu, doküman değişikliği yok. Eksik bağımlılıkları #3'ün yapılacaklar listesine aldım.
- **Ders çıkarımı:** Kodlamaya başlamadan önce dokümanla repodaki mevcut durumu karşılaştırmak, hangi işin bende olduğunu netleştiriyor.
