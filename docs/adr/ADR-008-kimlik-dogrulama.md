# ADR-008: Kimlik Doğrulama — JWT (httpOnly Çerez) + Argon2id

## Durum

Kabul Edildi *(Accepted)* — 2026-11-13

## Bağlam

- Kişisel notlar → her kullanıcı yalnızca kendi verisine erişmeli (güvenlik kriteri).
- Tek sayfa uygulaması (SPA) + REST API, aynı origin'den sunulacak.
- Token'ı `localStorage`'da tutmak XSS durumunda çalınmasına yol açar.
- Basit kalmalı: Ders projesi, sosyal giriş/SSO gereksiz.

## Karar

- Şifreler **Argon2id** ile hash'lenir (`argon2-cffi`); düz şifre hiçbir yerde saklanmaz/loglanmaz.
- Başarılı girişte imzalı **JWT** (HS256, `sub = user_id`, 8 saat geçerli) üretilir ve **`HttpOnly; SameSite=Strict; Path=/api`** çerezinde gönderilir (prod'da `Secure`). JS token'a erişemez.
- API yalnızca JSON kabul eder; `SameSite=Strict` + JSON-only istekler CSRF riskini pratikte ortadan kaldırır.
- Her korumalı uç nokta `current_user` bağımlılığı ile kullanıcıyı çözer; **yetkilendirme repository seviyesinde** (`owner_id` filtresi) yapılır, başka kullanıcının kaynağı 404 döner.
- Hatalı giriş mesajı geneldir ("E-posta veya şifre hatalı"). *(Should)* Giriş denemelerine rate limit.
- `JWT_SECRET` yalnızca ortam değişkeninden okunur.

## Değerlendirilen alternatifler

| Alternatif | Neden seçilmedi |
| --- | --- |
| **JWT `Authorization: Bearer` + localStorage** | XSS ile token çalınabilir. |
| **Sunucu taraflı oturum tablosu** | Daha güvenli iptal imkanı ama ek tablo ve her istekte DB sorgusu; bu ölçekte JWT yeterli. Çıkışta çerez silinir. |
| **Hazır kimlik sağlayıcı** (Auth0, Keycloak) | Kurulum ve bağımlılık yükü; dersin odağı değil. |
| **bcrypt** | Geçerli bir seçenek; Argon2id güncel OWASP önerisi. |

## Sonuçlar

**Avantajlar:**
- Token JS'ten erişilemez → XSS ile oturum çalma engellenir.
- Frontend'de token yönetimi kodu yok (tarayıcı çerezi otomatik gönderir).
- Yetkilendirme kuralı tek yerde (repository) ve testle kanıtlanır.

**Değiş tokuşlar:**
- JWT süresi dolmadan sunucu tarafında iptal edilemez (çıkış sadece çerezi siler). Kabul edilebilir: 8 saatlik süre.
- Refresh token yok; süre dolunca kullanıcı yeniden giriş yapar.
