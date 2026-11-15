"""Port arayüzleri (typing.Protocol).

Her alan kendi modülünde tanımlanır; böylece ekip üyeleri aynı dosyayı düzenlemez.
Bir port, onu ilk kullanan özellikle birlikte eklenir (kullanılmayan kod commit'lenmez):
- `system`: sağlık kontrolü (`ReadinessProbe`)
- ileride: `users`, `pages`, `links`, `ai` (ADR-006), `vector` (ADR-004) …
"""
