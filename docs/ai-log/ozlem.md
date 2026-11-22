# Yapay Zeka Kullanım Günlüğü — Özlem

> Özlem'in (İP-B) kayıtları. Şablon ve kurallar: [README.md](README.md). Kayıtlar tarih sırasıyla, en yenisi en altta.

### 2026-11-17 — Özlem: doküman okuma (#5)
- **Kim:** Özlem
- **Araç / model:** Claude (claude.ai, Claude Code)
- **Amaç:** İP-B ile ilgili dokümanları (README, KURALLAR, PLAN, architecture, domain-design, api-contract, ADR-008, ADR-009) okumak ve belirsiz yerleri bulmak.
- **Prompt (özet):** "Dokümanları bana tek tek, anlayacağım şekilde açıkla; ilk doküman PR'ım için düzeltilecek bir yer bul."
- **Sonuç:** domain-design.md § 4'teki `to_sections()` metodunun hangi işe ait olduğu netleştirildi. Düzenlemeleri, commit'leri ve PR'ı Özlem'in isteğiyle Claude yaptı; içeriği Özlem onayladı.
- **Yapay zekanın hataları / eksikleri:** Dokümanlarda `to_sections()` PageContent altında yazıyordu ama #6'da yoktu ve ADR-009 bölme işini `chunk_page`'e veriyordu.
- **Bizim müdahalemiz:** Belirsizliği gidermek için metodun #13 (parçalama) ile birlikte yazılacağını belirten bir not eklenmesine karar verdim.
- **Ders çıkarımı:** Görev kartı ile doküman arasında fark varsa kodlamaya başlamadan önce netleştirmek gerekir.
