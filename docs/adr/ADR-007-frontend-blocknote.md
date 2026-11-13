# ADR-007: Frontend — React + TypeScript + Vite + BlockNote

## Durum

Kabul Edildi *(Accepted)* — 2026-11-13

## Bağlam

- Notion klonunun en zor parçası **blok tabanlı editör**dür (`/` menüsü, sürükle-bırak bloklar, iç içe listeler, satır içi stiller). Sıfırdan yazmak projenin tamamını yiyebilir.
- Sayfalar arası bağlantı için editörde özel bir satır içi öğe (`@` ile sayfa bahsetme) gerekiyor.
- Ekibin frontend deneyimi sınırlı; kod yapay zeka desteğiyle yazılacak. Yaygın ve iyi belgelenmiş teknolojiler ajanların daha doğru kod üretmesini sağlar.

## Karar

- **React + TypeScript (strict) + Vite** tek sayfa uygulaması; React Router ile yönlendirme, TanStack Query ile veri çekme (önbellek, yeniden deneme).
- Editör: **[BlockNote](https://www.blocknotejs.org)**: ProseMirror/Tiptap üzerine kurulu, "Notion tarzı" hazır blok editörü. **Çekirdek paketler MPL-2.0** lisanslıdır. `@blocknote/xl-*` paketleri ayrı lisanslıdır (GPL-3.0 veya ticari) ve **ihtiyacımız olmadığı için kullanılmaz**.
- **Editör şeması kısıtlanır:** BlockNote varsayılan olarak tablo, görsel, video, ses, dosya ve açılır liste blokları da sunar. Editör yalnızca backend'in kabul ettiği bloklarla yapılandırılır: `paragraph`, `heading` (1–3), `bulletListItem`, `numberedListItem`, `checkListItem`, `codeBlock`, `quote` (domain-design § 4, R-06). Aksi halde kullanıcı backend'in reddedeceği (422) bir blok ekleyebilirdi.
- Sayfa bağlantısı için BlockNote'un özel satır içi içerik desteğiyle `pageMention` öğesi ve `@` tetikleyicili öneri menüsü. Bağlantıların güncel başlığı ve silinmiş olup olmadığı `/pages/titles` ile alınır.
- Otomatik kaydetme: 1 sn debounce, `version` ile iyimser kilitleme (409 → uyarı).
- Bileşenler `fetch` çağırmaz; tüm istekler tek bir tipli API istemcisinden (`src/api/`) geçer.
- Test: Vitest + Testing Library (API istemcisi mock'lanır). *(Should)* Playwright duman testleri.
- Geliştirmede Vite proxy `/api` isteklerini backend'e yönlendirir (aynı origin → çerez ve CORS sade).

## Değerlendirilen alternatifler

| Alternatif | Neden seçilmedi |
| --- | --- |
| **Sıfırdan editör** (contenteditable) | Çok büyük iş, hataya açık; projenin odağı (RAG, mimari, test) kaybolur. |
| **Editor.js** | Blok tabanlı ve hafif ama React entegrasyonu ve özel satır içi öğe desteği BlockNote kadar doğal değil. |
| **Tiptap (doğrudan)** | Çok esnek ama Notion tarzı arayüzü (blok tutamaçları, `/` menüsü) kendimiz kurmamız gerekir. |
| **Sunucu taraflı şablon** (Jinja / HTMX) | Zengin editör deneyimi için uygun değil. |

## Sonuçlar

**Avantajlar:**
- Notion deneyimi günler yerine saatler içinde hazır.
- İçerik JSON (blok dizisi) olarak gelir → PostgreSQL JSONB ile birebir uyumlu (ADR-003).
- TypeScript strict + eslint ile Sonar'da ölçülebilir kalite.

**Değiş tokuşlar:**
- Üçüncü taraf kütüphaneye bağımlılık; sürüm güncellemelerinde JSON yapısı değişebilir. Bu yüzden backend `PageContent` doğrulaması izin verilen türleri açıkça listeler ve BlockNote sürümü kilit dosyasıyla sabitlenir.
- BlockNote'un iç yapısı (ProseMirror) karmaşık; özel `pageMention` öğesi dışında içine girmiyoruz.
