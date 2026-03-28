# 📱 Play Reviewer

**Google Play Store Yorum Toplayıcı** — Mac web app

---

## Hızlı Başlangıç (Mac)

1. `PlayReviewer` klasörünü istediğiniz yere kopyalayın  
2. `launch.command` dosyasına **çift tıklayın**  
   - İlk açılışta Python bağımlılıkları otomatik kurulur (~1 dk)  
   - Tarayıcınızda uygulama otomatik açılır  
3. Kapatmak için Terminal penceresini kapatın

> **İlk açılışta "izin verilmemiş" hatası alırsanız:**  
> `launch.command` dosyasına sağ tıklayın → "Aç" → "Aç" deyin

---

## Özellikler

| Özellik | Detay |
|---------|-------|
| Paralel tarama | 15 uygulamayı aynı anda tara (8 thread) |
| Keyword filtresi | 500'e kadar keyword · OR / AND modu |
| Tarih presetleri | Son 7 gün / 1 ay / 3 ay / 6 ay / 12 ay / Özel |
| Puan filtresi | 1-5 yıldız |
| Export | CSV · Excel (uygulama bazlı çoklu sheet) |
| Yorum içi arama | Canlı arama filtresi |

---

## Manuel Kurulum (alternatif)

```bash
cd PlayReviewer
pip install -r requirements.txt
python server.py
```

Tarayıcıda: **http://localhost:5055**

---

## Klasör Yapısı

```
PlayReviewer/
├── server.py          ← Flask backend
├── requirements.txt
├── launch.command     ← Mac çift tıkla çalıştır
├── README.md
└── templates/
    └── index.html     ← Web arayüzü
```

---

## Notlar

- 100k yorum ≈ 10-15 dakika  
- Google Play rate limit uygularsa uygulama otomatik bekler  
- Sonuçlar sunucu RAM'inde tutulur; kapatınca sıfırlanır  
- Uygulamayı arka planda tutup birden fazla tarama yapabilirsiniz  
