# ESP32 ile Oda Sıcaklığı Ölçme Projesi

## Donanım

Projede ESP32 DevKit kartı ve DS18B20 dijital sıcaklık sensörü kullanıldı. Sensörün veri ucu GPIO 4 pinine bağlandı. Veri hattı ile 3,3 V arasına 4,7 kΩ'luk bir çekme (pull-up) direnci takıldı; bu direnç olmadan sensör okunamıyor. Kart, 2000 mAh'lik bir lityum pil ve 3,3 V regülatör ile besleniyor.

## Yazılım

Kod Arduino IDE ile yazıldı; OneWire ve DallasTemperature kütüphaneleri kullanıldı. Ölçülen sıcaklık Wi-Fi üzerinden MQTT ile `ev/salon/sicaklik` konusuna gönderiliyor. Ölçüm çözünürlüğü 12 bit seçildi, bu da yaklaşık 0,0625 °C hassasiyet veriyor.

## Enerji Tasarrufu

Kart her ölçümden sonra 10 dakika boyunca deep sleep moduna geçiyor. Uyku sırasında akım tüketimi yaklaşık 10 µA'e düşüyor; böylece pil ömrü birkaç günden birkaç haftaya çıkıyor. Uyandığında Wi-Fi'ye yeniden bağlanıp ölçümü gönderiyor ve tekrar uyuyor.
