"""Port arayüzleri (typing.Protocol).

Her alan kendi modülünde tanımlanır; böylece ekip üyeleri aynı dosyayı düzenlemez.
Bir port, onu ilk kullanan özellikle birlikte eklenir (kullanılmayan kod commit'lenmez):
- `system`: sağlık kontrolü (`ReadinessProbe`)
- `ai`: embedding ve sohbet modeli (`EmbeddingProvider`, `ChatModel`; ADR-006)
- `vector`: vektör indeksi (`VectorIndex`; ADR-004)
- `indexing`: indekslenmeyi bekleyen sayfalar ve parçalama (`PendingPages`, `Chunker`; ADR-005)
- ileride: `users`, `pages`, `links` …
"""
