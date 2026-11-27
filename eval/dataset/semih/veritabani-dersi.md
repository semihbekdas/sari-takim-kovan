# Veritabanı Dersi Notları

## Normalizasyon

Normalizasyon, tablolardaki veri tekrarını azaltmak ve güncelleme anomalilerini önlemek için yapılır.

- **1NF:** Her hücrede tek bir değer bulunur; tekrar eden gruplar ayrı tabloya taşınır.
- **2NF:** 1NF şartı sağlanır ve anahtar olmayan her sütun birincil anahtarın tamamına bağlıdır (kısmi bağımlılık yoktur).
- **3NF:** 2NF şartı sağlanır ve geçişli bağımlılık kaldırılır; anahtar olmayan bir sütun başka bir anahtar olmayan sütuna bağlı olamaz.
- **BCNF:** 3NF'nin daha sıkı halidir; her belirleyici bir aday anahtar olmalıdır.

## İndeksler

İndeks, sorgularda aramayı hızlandıran yardımcı bir yapıdır. Okumayı hızlandırır ama ekleme ve güncellemeyi biraz yavaşlatır. Hoca, sık filtrelenen sütunlara indeks koymamızı önerdi.

## Sınav

Vize sınavı 12 Kasım'da. Normalizasyon ve SQL JOIN türleri kesin çıkacak.
